from celery import Celery


from src.config.redis import RedisSettings

from src.config.connector import ConnectorSettings
from src.config.celery import CelerySettings


celery_config = CelerySettings()
redis_settings = RedisSettings()
celery_app = Celery(
    celery_config.CELERY_APP_NAME,
    broker=f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}//",
)

connector_settings = ConnectorSettings()
s3_available = connector_settings.S3_AVAILABLE == "True"
if s3_available:
    import boto3
    from src.connector.s3_connector import S3Connector
    from src.config.s3 import S3Settings
    from src.config.connector import ConnectorSettings

    try:
        connector_settings = ConnectorSettings()
        settings = S3Settings()
        s3_client = boto3.client(
            "s3",
            use_ssl=False,
            endpoint_url=settings.S3_END_POINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )

        bucket_name = settings.S3_BUCKET_NAME
        file_connector = S3Connector(s3_client, bucket_name)
    except Exception:
        raise

else:
    from minio import Minio
    from src.connector.minio_connector import MinioConnector
    from src.config.minio import MinioSettings

    try:
        minio_settings = MinioSettings()
        minio_client = Minio(
            endpoint=minio_settings.MINIO_END_POINT,
            access_key=minio_settings.MINIO_ACCESS_KEY,
            secret_key=minio_settings.MINIO_SECRET_KEY,
            secure=False,
        )

        file_connector = MinioConnector(minio_client=minio_client, bucket_name=minio_settings.MINIO_BUCKET_NAME)

    except Exception:
        raise
