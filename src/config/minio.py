from pydantic_settings import BaseSettings, SettingsConfigDict


class MinioSettings(BaseSettings):
    MINIO_BUCKET_NAME: str = "test"
    MINIO_END_POINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")
