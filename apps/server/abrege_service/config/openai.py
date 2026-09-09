import os
from typing import Any, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.utils.logger import logger_abrege as logger

# Renamed field: read the new (canonical, shared with ocr-api) name, fall back to the
# deprecated one with a warning so the deploy side can migrate at its own pace.
_DEPRECATED_ENV_ALIASES = {
    "OPENAI_API_BASE_URL": "OPENAI_API_BASE",
}

# The LLM hub remaps this generic alias to whichever concrete engine is live. Falling
# back to a concrete engine name (e.g. "mistral-small-3.1-24b-instruct-2503") breaks the
# moment the hub decommissions or renames that engine (hit in dev, 2026-07-25).
GENERIC_CHAT_ALIAS = "chat"


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow", from_attributes=True)

    OPENAI_API_KEY: str = "sk-XXXXXXXXXXXXXXXX"
    OPENAI_API_BASE_URL: Optional[str] = None
    OPENAI_API_MODEL: Optional[str] = GENERIC_CHAT_ALIAS
    OPENAI_VLM_MODEL_NAME: Optional[str] = GENERIC_CHAT_ALIAS
    # Per-feature model overrides for the side extractions (Q&A, entities/relationships,
    # semantic chunking, topic classification) dispatched alongside the summary. Each falls
    # back to OPENAI_API_MODEL (the summary's own model) when unset.
    QA_MODEL_NAME: Optional[str] = None
    ENTITY_MODEL_NAME: Optional[str] = None
    CHUNK_MODEL_NAME: Optional[str] = None
    TOPIC_MODEL_NAME: Optional[str] = None
    MAX_CONTEXT_SIZE: Optional[int] = 128_000  # Context size that the llm can handle

    @model_validator(mode="before")
    @classmethod
    def _apply_deprecated_env_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for new_key, old_key in _DEPRECATED_ENV_ALIASES.items():
            if data.get(new_key) is None and os.environ.get(old_key) is not None:
                logger.warning("Environment variable %s is deprecated, use %s instead.", old_key, new_key)
                data[new_key] = os.environ[old_key]

        return data

    @model_validator(mode="after")
    def _require_base_url(self) -> "OpenAISettings":
        if not self.OPENAI_API_BASE_URL:
            raise RuntimeError(
                "OPENAI_API_BASE_URL is not set. Refusing to silently send requests (and "
                "the API key) to the public OpenAI endpoint — set it explicitly to your LLM "
                "hub's base URL."
            )
        return self
