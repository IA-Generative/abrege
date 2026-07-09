from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_QUEUE_NAME: str = "redis-queue"
    # Authentication
    REDIS_PASSWORD: Optional[str] = None
    # TLS: set to True to use rediss:// scheme
    REDIS_TLS: bool = False
    # Sentinel: comma-separated "host:port" pairs, e.g. "sentinel1:26379,sentinel2:26379"
    # When set, REDIS_HOST/REDIS_PORT are ignored for the broker URL
    REDIS_SENTINEL_HOSTS: Optional[str] = None
    REDIS_SENTINEL_SERVICE_NAME: str = "mymaster"
    model_config = SettingsConfigDict(
        from_attributes=True, case_sensitive=True, env_file=".env", extra="allow"
    )
