import os
from typing import Any, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.logger import logger_abrege as logger

# Renamed fields: read the new (canonical, shared with ocr-api) name, fall back to the
# deprecated one with a warning so the deploy side can migrate at its own pace.
_DEPRECATED_ENV_ALIASES = {
    "REDIS_SENTINEL_MASTER_NAME": "REDIS_SENTINEL_SERVICE_NAME",
}


class RedisSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_QUEUE_NAME: str = "redis-queue"
    # Authentication
    REDIS_PASSWORD: Optional[str] = None
    # TLS: set to True to use rediss:// scheme
    REDIS_TLS: bool = False

    # Sentinel (optional) — when enabled, REDIS_HOST/REDIS_PORT are ignored and the
    # current master is resolved through the sentinel quorum instead.
    # REDIS_SENTINEL_ENABLED is the explicit toggle; if left unset, sentinel mode is
    # inferred from the presence of REDIS_SENTINEL_HOSTS.
    REDIS_SENTINEL_ENABLED: Optional[bool] = None
    REDIS_SENTINEL_HOSTS: Optional[str] = None  # "host1:26379,host2:26379,host3:26379"
    REDIS_SENTINEL_MASTER_NAME: str = "mymaster"
    # Password used to authenticate against the sentinel nodes themselves (may differ
    # from REDIS_PASSWORD, which authenticates against the resolved master). Falls
    # back to REDIS_PASSWORD when unset.
    REDIS_SENTINEL_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True, env_file=".env", extra="allow")

    @model_validator(mode="before")
    @classmethod
    def _apply_deprecated_env_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for new_key, old_key in _DEPRECATED_ENV_ALIASES.items():
            if data.get(new_key) is None and os.environ.get(old_key) is not None:
                logger.warning("Environment variable %s is deprecated, use %s instead.", old_key, new_key)
                data[new_key] = os.environ[old_key]

        if data.get("REDIS_SENTINEL_ENABLED") is None and os.environ.get("REDIS_SENTINEL_HOSTS"):
            data["REDIS_SENTINEL_ENABLED"] = True

        return data

    @property
    def sentinel_enabled(self) -> bool:
        return bool(self.REDIS_SENTINEL_ENABLED)

    def sentinel_hosts(self) -> list[tuple[str, int]]:
        if not self.REDIS_SENTINEL_HOSTS:
            return []
        hosts: list[tuple[str, int]] = []
        for entry in self.REDIS_SENTINEL_HOSTS.split(","):
            host, _, port = entry.strip().partition(":")
            hosts.append((host, int(port) if port else 26379))
        return hosts
