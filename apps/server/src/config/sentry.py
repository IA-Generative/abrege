from pydantic_settings import BaseSettings, SettingsConfigDict


class SentrySettings(BaseSettings):
    SENTRY_API_DSN: str = ""
    SENTRY_WORKER_DSN: str = ""
    SEND_DEFAULT_PII: bool = False
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")
