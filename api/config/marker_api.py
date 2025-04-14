from pydantic_settings import SettingsConfigDict, BaseSettings


class MarkerAPISettings(BaseSettings):
    MARKER_API_BASE_URL: str = "http://localhost:8000"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow", from_attributes=True)
