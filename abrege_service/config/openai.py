from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow", from_attributes=True)
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    OPENAI_API_MODEL: Optional[str] = "gemma3"
    OPENAI_VLM_MODEL_NAME: Optional[str] = "mistral-small-3.1-24b-instruct-2503"
    MAX_CONTEXT_SIZE: Optional[int] = 128_000  # Context size that the llm can handle
    TOKENIZER_MODEL_NAME: Optional[str] = (
        "gpt-4"  # For counting number of token the system has, please make sure the tokenizer is available in hugging-face
    )
