from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow", from_attributes=True)
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    OPENAI_API_MODEL: Optional[str] = "gemma3"
    MAX_CONTEXT_SIZE: Optional[int] = 128_000  # for qwen
