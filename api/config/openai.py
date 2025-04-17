from typing import Optional
from .base import Base


class OpenAISettings(Base):
    OPENAI_API_BASE: str
    OPENAI_API_KEY: str
    DEFAULT_MODEL_NAME: Optional[str] = "gemma3"
