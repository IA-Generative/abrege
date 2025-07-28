from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    S3_BUCKET_NAME: str = "test"
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")
