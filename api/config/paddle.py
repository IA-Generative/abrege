from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    PADDLE_OCR_URL: str = "http://localhost:8000"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow", from_attributes=True)
