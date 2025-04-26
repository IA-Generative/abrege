from pydantic_settings import BaseSettings, SettingsConfigDict


class S3Settings(BaseSettings):
    S3_BUCKET_NAME: str = "test"
    S3_END_POINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "S3admin"
    S3_SECRET_KEY: str = "S3admin"
    S3_REGION: str = "fr-par"
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")
