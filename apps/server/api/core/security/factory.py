import logging
import os
import warnings
from api.core.security import keycloak_client
from api.core.security.token import BaseVerifyToken, RequestContext, parse_header_context
from fastapi import HTTPException, Request, status


class AllowAllAccess(BaseVerifyToken):
    def __init__(self, verify_token=True):
        super().__init__(verify_token, is_fastapi=True)
        warnings.warn(message="YOU USE DEV MODE PLEASE DON'T USE THAT IN PRODUCTION")

    def verify(self, ctx: RequestContext) -> bool:
        ctx.user_id = "dev"
        return True


class DevToken(BaseVerifyToken):
    def __init__(self):
        super().__init__(verify_token=True, is_fastapi=True)
        warnings.warn(message="YOU USE DEV MODE PLEASE DON'T USE THAT IN PRODUCTION")
        self.user_info = {
            "token1": RequestContext(user_id="test1", email="r@exemple.com", roles=[], token="token1"),
            "token2": RequestContext(user_id="test2", email="r@exemple.com", roles=[], token="token2"),
        }

    def verify(self, ctx: RequestContext):
        if ctx.token in self.user_info:
            current_user = self.user_info[ctx.token]
            return ctx.user_id == current_user.user_id

        return False


class KeycloakToken(BaseVerifyToken):
    """Authenticates a request either via a service `Authorization: Bearer <Keycloak token>`
    header (service-to-service, e.g. the SDK using a client-credentials token), or via the
    BFF session cookie set by `/api/auth/callback`.

    The browser never holds a Keycloak token: the frontend only ever sends the opaque
    session cookie, and the actual access/refresh tokens stay server-side in Redis
    (see `api.core.security.session.SessionStore`).
    """

    def __init__(self):
        super().__init__(verify_token=True, is_fastapi=True)
        self.keycloak_openid = keycloak_client.keycloak_openid

    def verify(self, ctx: RequestContext) -> bool:
        """Vérifie un token Keycloak (Bearer) via introspection et remplit ctx.

        Returns immediately without a network call when there is no bearer token: this is
        also the browser/cookie-session path (see `__call__`), which must not pay a round
        trip to Keycloak's introspection endpoint on every single request.
        """
        if not ctx.token:
            return False
        try:
            user_info = self.keycloak_openid.introspect(ctx.token)
            logging.debug(f"Token info: {user_info.keys()}")
            if user_info.get("active") is False:
                return False

            ctx.user_id = user_info.get("sub", "")
            ctx.email = user_info.get("email", "")
            ctx.groups = user_info.get("groups", [])
            ctx.roles = user_info.get("realm_access", {}).get("roles", [])
            ctx.is_admin = "admin" in ctx.roles or "realm-admin" in ctx.roles

            return True

        except Exception:
            logging.exception("Erreur lors de la vérification du token")
            return False

    def __call__(self, request: Request) -> RequestContext:
        ctx = parse_header_context(request, is_fastapi=self.is_fastapi)

        # `self.verify` is called unconditionally (not only when a bearer token is present)
        # so that overriding it - as the test suite does via `TokenVerifier.verify = ...` -
        # fully controls the outcome, same as the inherited `BaseVerifyToken.__call__`.
        if self.verify(ctx):
            return ctx

        sid = request.cookies.get(keycloak_client.keycloak_settings.SESSION_COOKIE_NAME)
        session = keycloak_client.session_store.get(sid) if sid else None
        if session:
            session = keycloak_client.session_store.ensure_fresh(sid, session)

        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")

        ctx.user_id = session.user_id
        ctx.email = session.email
        ctx.roles = session.roles
        ctx.groups = session.groups
        ctx.is_admin = session.is_admin
        ctx.token = session.access_token
        return ctx


SECURITY_FACTORY: dict[str, BaseVerifyToken] = {
    "full-access": AllowAllAccess,
    "dev": DevToken,
    "keycloak": KeycloakToken,
}

TokenVerifier: BaseVerifyToken = SECURITY_FACTORY[os.environ.get("VERIFY_TOKEN_MODEL", "keycloak")]()
