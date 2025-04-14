from pydantic_settings import SettingsConfigDict, BaseSettings


class Settings(BaseSettings):
    PADDLE_OCR_URL: str
    PADDLE_OCR_TOKEN: str
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=True, extra='allow', from_attributes=True)
