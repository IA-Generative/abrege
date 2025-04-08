from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    PADDLE_OCR_URL: str
    PADDLE_OCR_TOKEN: str
    model_config = SettingsConfigDict(from_attributes=True, case_sensitive=True)
