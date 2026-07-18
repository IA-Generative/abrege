from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_QUEUE_NAME: str = "redis-queue"
    # Authentication
    REDIS_PASSWORD: Optional[str] = None
    # TLS: set to True to use rediss:// scheme
    REDIS_TLS: bool = False
    # Sentinel: comma-separated "host:port" pairs, e.g. "sentinel1:26379,sentinel2:26379"
    # When set, REDIS_HOST/REDIS_PORT are ignored and the current master is resolved
    # through the sentinel quorum instead.
    REDIS_SENTINEL_HOSTS: Optional[str] = None
    REDIS_SENTINEL_SERVICE_NAME: str = "mymaster"
    # Password used to authenticate against the sentinel nodes themselves (may differ
    # from REDIS_PASSWORD, which authenticates against the resolved master). Falls
    # back to REDIS_PASSWORD when unset.
    REDIS_SENTINEL_PASSWORD: Optional[str] = None
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")

    def sentinel_hosts(self) -> list[tuple[str, int]]:
        if not self.REDIS_SENTINEL_HOSTS:
            return []
        hosts: list[tuple[str, int]] = []
        for entry in self.REDIS_SENTINEL_HOSTS.split(","):
            host, _, port = entry.strip().partition(":")
            hosts.append((host, int(port) if port else 26379))
        return hosts
