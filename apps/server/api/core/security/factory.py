import logging
import os
import warnings
from api.core.security.token import BaseVerifyToken, RequestContext
from keycloak import KeycloakOpenID


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
    def __init__(self):
        super().__init__(verify_token=True, is_fastapi=True)

        # Configuration Keycloak depuis les variables d'environnement
        self.keycloak_url = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
        self.realm_name = os.environ.get("KEYCLOAK_REALM", "master")
        self.client_id = os.environ.get("KEYCLOAK_CLIENT_ID", "your-client-id")
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.keycloak_url,
            client_id=self.client_id,
            realm_name=self.realm_name,
            client_secret_key=os.environ.get("KEYCLOAK_CLIENT_SECRET", "secret"),
        )

    def verify(self, ctx: RequestContext) -> bool:
        """Vérifie le token JWT avec Keycloak et remplit ctx avec les infos utilisateur"""
        try:
            user_info = self.keycloak_openid.introspect(ctx.token)
            logging.debug(f"Token info: {user_info.keys()}")
            if user_info.get("active") is False:
                return False

            # Remplir le contexte avec les informations récupérées
            ctx.user_id = user_info.get("sub", "")  # Subject = user ID
            ctx.email = user_info.get("email", "")
            ctx.groups = user_info.get("groups", [])

            # Récupérer les rôles (peut varier selon la config Keycloak)
            ctx.roles = user_info.get("realm_access", {}).get("roles", [])
            # Ou si les rôles sont dans realm_access :
            # ctx.roles = user_info.get("realm_access", {}).get("roles", [])

            # Déterminer si l'utilisateur est admin
            ctx.is_admin = "admin" in ctx.roles or "realm-admin" in ctx.roles

            return True

        except Exception as e:
            logging.error(f"Erreur lors de la vérification du token: {e}")
            return False


SECURITY_FACTORY: dict[str, BaseVerifyToken] = {
    "full-access": AllowAllAccess,
    "dev": DevToken,
    "keycloak": KeycloakToken,
}

TokenVerifier: BaseVerifyToken = SECURITY_FACTORY[os.environ.get("VERIFY_TOKEN_MODEL", "keycloak")]()
