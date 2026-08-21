from celery import Celery
import boto3
import redis
from redis.sentinel import Sentinel
from src.connector.s3_connector import S3Connector
from src.connector.redis_connector import RedisConnector
from src.connector.broker_connector import BrokerConnector
from src.config.s3 import S3Settings
from src.config.connector import ConnectorSettings
from src.config.redis import RedisSettings
from src.config.celery import CelerySettings
from src.utils.logger import logger_abrege
from src.utils.url import sanitize_broker_url


def _redis_scheme(settings: RedisSettings) -> str:
    return "rediss" if settings.REDIS_TLS else "redis"


def _build_broker_url(settings: RedisSettings) -> tuple[str, dict]:
    """Build the Celery broker URL and transport options.

    Supports plain redis/rediss, and Sentinel (the actual master is resolved
    at connection time by Celery's own redis-sentinel transport).
    """
    if settings.REDIS_SENTINEL_HOSTS:
        password = settings.REDIS_SENTINEL_PASSWORD or settings.REDIS_PASSWORD
        auth = f":{password}@" if password else ""
        urls = ";".join(f"sentinel://{auth}{host}:{port}/{settings.REDIS_DB}" for host, port in settings.sentinel_hosts())
        transport_options = {
            "master_name": settings.REDIS_SENTINEL_SERVICE_NAME,
            "sentinel_kwargs": ({"password": password} if password else {}),
        }
        return urls, transport_options

    auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"{_redis_scheme(settings)}://{auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}", {}


def _build_redis_client(settings: RedisSettings) -> redis.Redis:
    """Build a plain redis.Redis client, resolving the current master via Sentinel if enabled."""
    if settings.REDIS_SENTINEL_HOSTS:
        sentinel_password = settings.REDIS_SENTINEL_PASSWORD or settings.REDIS_PASSWORD
        sentinel = Sentinel(
            settings.sentinel_hosts(),
            socket_connect_timeout=2,
            sentinel_kwargs={
                "password": sentinel_password,
                "ssl": settings.REDIS_TLS,
            },
        )
        return sentinel.master_for(
            settings.REDIS_SENTINEL_SERVICE_NAME,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            ssl=settings.REDIS_TLS,
            socket_connect_timeout=2,
        )

    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        ssl=settings.REDIS_TLS,
        socket_connect_timeout=2,
    )


celery_config = CelerySettings()
redis_settings = RedisSettings()

broker_url, broker_transport_options = _build_broker_url(redis_settings)

celery_app = Celery(
    celery_config.CELERY_APP_NAME,
    broker=broker_url,
)
if broker_transport_options:
    celery_app.conf.broker_transport_options = broker_transport_options
    celery_app.conf.result_backend_transport_options = broker_transport_options

# Trace de demarrage : sans elle, une absence de mot de passe est indetectable
# autrement qu'en lisant les erreurs de publication une a une.
broker_has_auth = "@" in broker_url
logger_abrege.info(
    f"Celery broker: {sanitize_broker_url(broker_url)} "
    f"| auth={'yes' if broker_has_auth else 'no'} "
    f"| sentinel={bool(redis_settings.REDIS_SENTINEL_HOSTS)}"
)
if not broker_has_auth:
    logger_abrege.warning(
        "Broker Celery configure SANS authentification : tout Redis exigeant un mot de passe rejettera les publications avec NOAUTH"
    )

redis_client = _build_redis_client(redis_settings)
redis_connector = RedisConnector(redis_client=redis_client)
broker_connector = BrokerConnector(celery_app=celery_app)

connector_settings = ConnectorSettings()

try:
    settings = S3Settings()
    s3_client = boto3.client(
        "s3",
    )

    bucket_name = settings.AWS_BUCKET_NAME
    file_connector = S3Connector(s3_client, bucket_name)
except Exception:
    raise
