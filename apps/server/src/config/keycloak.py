from typing import Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class KeycloakSettings(BaseSettings):
    KEYCLOAK_URL: str = "http://localhost:8080"
    # Browser-facing issuer URL. Falls back to KEYCLOAK_URL when unset, which is correct
    # whenever Keycloak is reachable at the same address from both the backend and the
    # browser (a single public HTTPS domain in production). Only needs to differ in local
    # docker compose, where the backend reaches Keycloak via the service name but the
    # browser must be redirected to the host-mapped port instead.
    KEYCLOAK_PUBLIC_URL: Optional[str] = None
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = "your-client-id"
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None

    # Fixed redirect_uri sent to Keycloak; must exactly match a registered client redirect URI.
    BACKEND_PUBLIC_URL: str = "http://localhost:5000"
    # Where the browser lands after a successful/failed login.
    FRONTEND_URL: str = "http://localhost:8082"

    SESSION_COOKIE_NAME: str = "abrege_session"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    SESSION_TTL_SECONDS: int = 7 * 24 * 60 * 60

    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")

    @field_validator("FRONTEND_URL", "BACKEND_PUBLIC_URL", mode="after")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        # A trailing slash here doubles up wherever it's concatenated with a path
        # ("//abrege", or BACKEND_PUBLIC_URL + "/api/auth/callback" -> ".../api/auth/callback"
        # with a leading double slash that 404s at the ingress) or compared as a CORS
        # `Origin` header (which never has one).
        return value.rstrip("/")

    @property
    def public_url(self) -> str:
        return self.KEYCLOAK_PUBLIC_URL or self.KEYCLOAK_URL

    @property
    def callback_url(self) -> str:
        return f"{self.BACKEND_PUBLIC_URL}/api/auth/callback"
