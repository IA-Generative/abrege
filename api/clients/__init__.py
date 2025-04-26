from .marker_client import MarkerAPIClient
from ..config.marker_api import MarkerAPISettings
from src.config.celery import CelerySettings
from src.config.redis import RedisSettings
from celery import Celery

marker_api_setting = MarkerAPISettings()

client_marker = MarkerAPIClient(base_url=marker_api_setting.MARKER_API_BASE_URL)

celery_config = CelerySettings()
redis_settings = RedisSettings()
celery_app = Celery(
    celery_config.CELERY_APP_NAME,
    broker=f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}//",
)
