from keycloak import KeycloakOpenID

from api.core.security.session import SessionStore
from src.clients import redis_client
from src.config.keycloak import KeycloakSettings

keycloak_settings = KeycloakSettings()

keycloak_openid = KeycloakOpenID(
    server_url=keycloak_settings.KEYCLOAK_URL,
    client_id=keycloak_settings.KEYCLOAK_CLIENT_ID,
    realm_name=keycloak_settings.KEYCLOAK_REALM,
    client_secret_key=keycloak_settings.KEYCLOAK_CLIENT_SECRET,
)

session_store = SessionStore(
    redis_client=redis_client,
    keycloak_openid=keycloak_openid,
    ttl_seconds=keycloak_settings.SESSION_TTL_SECONDS,
)
