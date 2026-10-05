import base64
import hashlib
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from api.core.security import keycloak_client
from api.core.security.claims import extract_identity
from api.docs import TOO_MANY_REQUESTS, UNAUTHORIZED, ErrorResponse
from src.utils.logger import logger_abrege as logger

router = APIRouter(tags=["Auth"])


class PasswordGrantRequest(BaseModel):
    username: str = Field(description="Keycloak username")
    password: str = Field(description="Keycloak password")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token obtained from `POST /api/auth/token`")


class PasswordGrantResponse(BaseModel):
    access_token: str = Field(description="Keycloak access token, to send as `Authorization: Bearer <access_token>`")
    expires_in: int = Field(description="Lifetime of the access token, in seconds")
    refresh_token: str = Field(description="Token to get a new access token with `POST /api/auth/refresh`")
    refresh_expires_in: int = Field(description="Lifetime of the refresh token, in seconds")
    token_type: str = Field("Bearer", description="Always `Bearer`")


class CurrentUser(BaseModel):
    id: str | None = Field(None, description="Identifier of the user")
    email: str | None = Field(None, description="Email address of the user")
    firstName: str | None = Field(None, description="First name of the user")
    lastName: str | None = Field(None, description="Last name of the user")
    groups: list[str] | None = Field(None, description="Groups the user belongs to")


class LogoutResponse(BaseModel):
    redirectUrl: str = Field(description="Keycloak end-session URL the browser should be sent to to finish logging out")

_keycloak_openid = keycloak_client.keycloak_openid
_keycloak_settings = keycloak_client.keycloak_settings
_session_store = keycloak_client.session_store

# Each hit writes an unauthenticated `PendingAuth` entry to Redis (5 min TTL); bounding
# it per caller stops that from being spammed into unbounded growth between expiries.
_LOGIN_RATE_LIMIT = 20
_LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60


def _is_safe_internal_path(path: str | None) -> bool:
    """Only accept app-relative paths: an absolute or protocol-relative value
    ("//evil.tld") would turn the post-login redirect into an open redirect."""
    return bool(path) and path.startswith("/") and not path.startswith("//")


def _is_same_origin(request: Request) -> bool:
    """CSRF defense in depth for state-changing routes, on top of `SameSite=Lax`. Rejects
    only requests that positively identify as cross-site; missing headers (old browsers,
    non-browser clients) fall through to `SameSite` rather than fail closed here."""
    sec_fetch_site = request.headers.get("sec-fetch-site")
    if sec_fetch_site is not None:
        return sec_fetch_site in ("same-origin", "same-site", "none")

    origin = request.headers.get("origin")
    if origin is not None:
        return origin.rstrip("/") == _keycloak_settings.FRONTEND_URL

    return True


def _build_pkce_pair() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def _end_session_url(id_token: str | None) -> str:
    """Built by hand for the same reason as `login()`'s auth_url: `well_known()` resolves
    against the server-to-server `KEYCLOAK_URL`, not the browser-facing `KEYCLOAK_PUBLIC_URL`.

    Ending the local session and revoking the refresh token (done by the caller) is not
    enough to log the user out: Keycloak's own SSO cookie survives that, and the next
    `/api/auth/login` silently signs the browser back in. Redirecting it here to
    `end_session_endpoint` is what actually ends that SSO session.
    """
    params = {
        "client_id": _keycloak_settings.KEYCLOAK_CLIENT_ID,
        "post_logout_redirect_uri": _keycloak_settings.FRONTEND_URL,
    }
    if id_token:
        # Lets Keycloak end the session without an intermediate confirmation prompt.
        params["id_token_hint"] = id_token
    return f"{_keycloak_settings.public_url}/realms/{_keycloak_settings.KEYCLOAK_REALM}/protocol/openid-connect/logout?{urlencode(params)}"


def _set_session_cookie(response: Response, sid: str) -> None:
    response.set_cookie(
        key=_keycloak_settings.SESSION_COOKIE_NAME,
        value=sid,
        httponly=True,
        secure=_keycloak_settings.SESSION_COOKIE_SECURE,
        samesite=_keycloak_settings.SESSION_COOKIE_SAMESITE,
        path="/",
        max_age=_keycloak_settings.SESSION_TTL_SECONDS,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_keycloak_settings.SESSION_COOKIE_NAME,
        path="/",
        secure=_keycloak_settings.SESSION_COOKIE_SECURE,
        samesite=_keycloak_settings.SESSION_COOKIE_SAMESITE,
    )


@router.get(
    "/login",
    summary="Log in (browser)",
    description="""Start the browser login: the backend runs the OAuth2 Authorization Code + PKCE flow and redirects (`307`) to Keycloak.
After a successful login, `GET /api/auth/callback` sets the session cookie and sends the user back to the frontend.

Meant to be opened as a full page navigation, not called with `fetch`. For scripts, use `POST /api/auth/token`.""",
    responses={
        307: {"description": "Redirect to the Keycloak login page."},
        **TOO_MANY_REQUESTS,
    },
)
async def login(
    request: Request,
    redirect: str | None = Query(default=None, description="App-relative path to return to after login (e.g. `/tasks`). Absolute URLs are ignored."),
):
    # `request.client.host` is whatever peer terminates the TCP connection - the load
    # balancer/reverse proxy in front of this service, unless it forwards the real client
    # IP some other way. Good enough to bound abuse from a single connection; not a
    # substitute for rate limiting at the edge.
    client_ip = request.client.host if request.client else "unknown"
    if not _session_store.check_rate_limit(f"login:{client_ip}", _LOGIN_RATE_LIMIT, _LOGIN_RATE_LIMIT_WINDOW_SECONDS):
        logger.warning("Rate-limiting /api/auth/login for %s", client_ip)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="TOO_MANY_REQUESTS")

    next_path = redirect if _is_safe_internal_path(redirect) else "/"

    code_verifier, code_challenge = _build_pkce_pair()
    state = secrets.token_urlsafe(32)
    _session_store.save_pending(state, code_verifier, next_path)

    # Built by hand rather than via `KeycloakOpenID.auth_url()`: that helper resolves the
    # authorization endpoint through `well_known()` on the *server-to-server* connection,
    # which in local docker compose points at the internal `keycloak:8080` hostname - not
    # reachable from the browser. `KEYCLOAK_PUBLIC_URL` is the address we redirect the
    # browser to instead.
    params = {
        "client_id": _keycloak_settings.KEYCLOAK_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": _keycloak_settings.callback_url,
        "scope": "openid profile email",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = f"{_keycloak_settings.public_url}/realms/{_keycloak_settings.KEYCLOAK_REALM}/protocol/openid-connect/auth?{urlencode(params)}"
    return RedirectResponse(auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.post(
    "/token",
    response_model=PasswordGrantResponse,
    summary="Get an access token (scripts, SDK)",
    description="""Exchange a username and password for a Keycloak access token (Resource Owner Password Credentials grant), entirely
server-side: the client secret never leaves the backend. Use the returned token as `Authorization: Bearer <access_token>` on the
other endpoints, and renew it with `POST /api/auth/refresh`. No session cookie is created.""",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials."},
        **TOO_MANY_REQUESTS,
    },
)
async def token(request: Request, body: PasswordGrantRequest):
    """Non-browser counterpart to `/login`, for the SDK/scripts: exchanges a
    username/password for a Keycloak access token via the Resource Owner Password
    Credentials grant, entirely server-side - the client secret never leaves this
    backend, and the caller never talks to Keycloak directly.

    The returned access token is a genuine Keycloak token, accepted on subsequent API
    calls as `Authorization: Bearer <token>` by `KeycloakToken.verify()`
    (`api/core/security/factory.py`), the same way a service token is - it is not
    persisted as a BFF session here, unlike `/callback`.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not _session_store.check_rate_limit(f"token:{client_ip}", _LOGIN_RATE_LIMIT, _LOGIN_RATE_LIMIT_WINDOW_SECONDS):
        logger.warning("Rate-limiting /api/auth/token for %s", client_ip)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="TOO_MANY_REQUESTS")

    try:
        token_response = _keycloak_openid.token(
            username=body.username,
            password=body.password,
            scope="openid profile email",
        )
    except Exception:
        logger.warning("Password grant failed for %s", client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")

    return PasswordGrantResponse(
        access_token=token_response["access_token"],
        expires_in=token_response["expires_in"],
        refresh_token=token_response["refresh_token"],
        refresh_expires_in=token_response["refresh_expires_in"],
    )


@router.post(
    "/refresh",
    response_model=PasswordGrantResponse,
    summary="Refresh an access token",
    description="Exchange the refresh token obtained from `POST /api/auth/token` for a fresh access token, entirely server-side.",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token."},
        **TOO_MANY_REQUESTS,
    },
)
async def refresh(request: Request, body: RefreshTokenRequest):
    """Exchange a refresh token (obtained from `/token`) for a fresh access token,
    entirely server-side - same trust boundary as `/token`, the SDK/scripts
    counterpart to how `SessionStore.ensure_fresh` refreshes browser sessions.
    """
    client_ip = request.client.host if request.client else "unknown"
    if not _session_store.check_rate_limit(f"refresh:{client_ip}", _LOGIN_RATE_LIMIT, _LOGIN_RATE_LIMIT_WINDOW_SECONDS):
        logger.warning("Rate-limiting /api/auth/refresh for %s", client_ip)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="TOO_MANY_REQUESTS")

    try:
        token_response = _keycloak_openid.refresh_token(body.refresh_token)
    except Exception:
        logger.warning("Refresh token exchange failed for %s", client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INVALID_REFRESH_TOKEN")

    return PasswordGrantResponse(
        access_token=token_response["access_token"],
        expires_in=token_response["expires_in"],
        refresh_token=token_response["refresh_token"],
        refresh_expires_in=token_response["refresh_expires_in"],
    )


@router.get(
    "/callback",
    summary="Login callback (Keycloak)",
    description="""Redirect target of Keycloak after the login. Exchanges the authorization code, creates the server-side session, sets the
`httpOnly` session cookie and redirects (`302`) to the frontend. On any failure it redirects to the frontend without a session.

Called by Keycloak through the browser, not by API clients.""",
    responses={302: {"description": "Redirect to the frontend (with the session cookie on success)."}},
)
async def callback(
    code: str | None = Query(default=None, description="Authorization code issued by Keycloak."),
    state: str | None = Query(default=None, description="Anti-CSRF `state` value generated by `GET /api/auth/login`."),
    error: str | None = Query(default=None, description="Error code returned by Keycloak when the login failed."),
):
    if error or not code or not state:
        logger.warning(
            "Keycloak auth callback failed: error=%s code_present=%s state_present=%s",
            error,
            bool(code),
            bool(state),
        )
        return RedirectResponse(_keycloak_settings.FRONTEND_URL, status_code=status.HTTP_302_FOUND)

    pending = _session_store.pop_pending(state)
    if not pending:
        logger.warning("Rejecting auth callback with unknown/expired/reused state")
        return RedirectResponse(_keycloak_settings.FRONTEND_URL, status_code=status.HTTP_302_FOUND)

    try:
        token_response = _keycloak_openid.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri=_keycloak_settings.callback_url,
            code_verifier=pending.code_verifier,
        )
        # `userinfo()` rather than `introspect()`: introspection requires the authenticating
        # client to be in the token's `aud`, which a client's own token never is (only ever
        # in `azp`) - this client would reject its own tokens. userinfo has no such
        # restriction and the access token was just received straight from the token
        # endpoint over an authenticated TLS channel, so there's nothing left to validate.
        # A rejected/expired token 401s here and falls into the except below rather than
        # silently producing an empty-but-valid identity.
        claims = _keycloak_openid.userinfo(token_response["access_token"])
        identity = extract_identity(claims, _keycloak_settings.KEYCLOAK_CLIENT_ID)
        if identity is None:
            logger.warning("Keycloak userinfo response had no subject, rejecting callback")
            return RedirectResponse(_keycloak_settings.FRONTEND_URL, status_code=status.HTTP_302_FOUND)
        sid = _session_store.create(token_response, identity)
    except Exception:
        logger.exception("Keycloak token exchange failed")
        return RedirectResponse(_keycloak_settings.FRONTEND_URL, status_code=status.HTTP_302_FOUND)

    response = RedirectResponse(
        f"{_keycloak_settings.FRONTEND_URL}{pending.next_path}",
        status_code=status.HTTP_302_FOUND,
    )
    _set_session_cookie(response, sid)
    return response


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Log out (browser)",
    description="""End the browser session: revokes the Keycloak refresh token, deletes the server-side session and clears the cookie.
Returns the Keycloak end-session URL the browser should navigate to. Only accepted from the app's own origin.""",
    responses={403: {"model": ErrorResponse, "description": "The request does not come from the app's own origin."}},
)
async def logout(request: Request, response: Response):
    if not _is_same_origin(request):
        logger.warning("Rejecting cross-site logout request")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    sid = request.cookies.get(_keycloak_settings.SESSION_COOKIE_NAME)
    id_token = None
    if sid:
        session = _session_store.get(sid)
        if session:
            id_token = session.id_token or None
            try:
                _keycloak_openid.logout(session.refresh_token)
            except Exception:
                # Local session is dropped regardless - a Keycloak-side revocation failure
                # (e.g. already-expired refresh token) must not leave the user stuck logged in.
                logger.warning("Keycloak refresh token revocation failed", exc_info=True)
        _session_store.delete(sid)
    _clear_session_cookie(response)
    return {"redirectUrl": _end_session_url(id_token)}


@router.get(
    "/me",
    response_model=CurrentUser,
    summary="Current user",
    description="Return the user of the current browser session. Used by the frontend to know whether the user is logged in.",
    responses={**UNAUTHORIZED},
)
async def me(request: Request):
    sid = request.cookies.get(_keycloak_settings.SESSION_COOKIE_NAME)
    session = _session_store.get(sid) if sid else None
    if session:
        session = _session_store.ensure_fresh(sid, session)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")

    return {
        "id": session.user_id,
        "email": session.email,
        "firstName": session.first_name,
        "lastName": session.last_name,
        "groups": session.groups,
    }
