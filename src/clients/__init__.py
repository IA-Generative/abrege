from celery import Celery
import boto3
from src.connector.s3_connector import S3Connector
from src.config.s3 import S3Settings
from src.config.connector import ConnectorSettings
from src.config.redis import RedisSettings
from src.config.celery import CelerySettings


celery_config = CelerySettings()
redis_settings = RedisSettings()
celery_app = Celery(
    celery_config.CELERY_APP_NAME,
    broker=f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}//",
)

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
