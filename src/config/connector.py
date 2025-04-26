from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectorSettings(BaseSettings):
    S3_AVAILABLE: Literal["True", "False"] = "False"
    MINIO_AVAILABLE: Literal["True", "False"] = "True"
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")
