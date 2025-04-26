from src.config.celery import CelerySettings
from src.config.redis import RedisSettings
from celery import Celery


celery_config = CelerySettings()
redis_settings = RedisSettings()
celery_app = Celery(
    celery_config.CELERY_APP_NAME,
    broker=f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}//",
)
