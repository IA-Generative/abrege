from celery import Celery
import boto3
from src.connector.s3_connector import S3Connector
from src.config.s3 import S3Settings
from src.config.connector import ConnectorSettings
from src.config.redis import RedisSettings
from src.config.celery import CelerySettings


def _build_broker_url(settings: RedisSettings) -> str:
    scheme = "rediss" if settings.REDIS_TLS else "redis"
    auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""

    if settings.REDIS_SENTINEL_HOSTS:
        hosts = [h.strip() for h in settings.REDIS_SENTINEL_HOSTS.split(",")]
        parts = [f"sentinel://{auth}{host}//" for host in hosts]
        return ";".join(parts)

    return f"{scheme}://{auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}//"


celery_config = CelerySettings()
redis_settings = RedisSettings()

celery_app = Celery(
    celery_config.CELERY_APP_NAME,
    broker=_build_broker_url(redis_settings),
)

if redis_settings.REDIS_SENTINEL_HOSTS:
    celery_app.conf.broker_transport_options = {
        "master_name": redis_settings.REDIS_SENTINEL_SERVICE_NAME,
    }

connector_settings = ConnectorSettings()

try:
    settings = S3Settings()
    s3_client = boto3.client(
        "s3",
    )

    bucket_name = settings.S3_BUCKET_NAME
    file_connector = S3Connector(s3_client, bucket_name)
except Exception:
    raise
