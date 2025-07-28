from pydantic_settings import BaseSettings, SettingsConfigDict


class CelerySettings(BaseSettings):
    CELERY_APP_NAME: str = "default"
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")
