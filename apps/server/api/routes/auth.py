import base64
import hashlib
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from api.core.security import keycloak_client
from api.core.security.claims import extract_identity
from src.utils.logger import logger_abrege as logger

router = APIRouter(tags=["Auth"])

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
    return (
        f"{_keycloak_settings.public_url}/realms/{_keycloak_settings.KEYCLOAK_REALM}"
        f"/protocol/openid-connect/logout?{urlencode(params)}"
    )


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


@router.get("/login")
async def login(request: Request, redirect: str | None = Query(default=None)):
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
    auth_url = (
        f"{_keycloak_settings.public_url}/realms/{_keycloak_settings.KEYCLOAK_REALM}"
        f"/protocol/openid-connect/auth?{urlencode(params)}"
    )
    return RedirectResponse(auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/callback")
async def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
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


@router.post("/logout")
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


@router.get("/me")
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
