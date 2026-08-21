from datetime import datetime

import celery

from src.schemas.health import Health, HealtStatus


class BrokerConnector:
    """Sonde de santé de la connexion au broker Celery.

    Distincte de RedisConnector : le broker est joint via kombu, avec sa propre
    URL et ses propres identifiants. Il peut donc échouer alors qu'un client
    Redis simple réussit — c'est précisément le cas qui est resté invisible
    pendant l'incident NOAUTH de juillet/août 2026.
    """

    def __init__(self, celery_app: celery.Celery, timeout: float = 2.0):
        self.celery_app = celery_app
        self.timeout = timeout
        self.up_time = datetime.now().isoformat()

    def get_health(self) -> Health:
        try:
            with self.celery_app.connection_for_write() as connection:
                connection.ensure_connection(max_retries=0, timeout=self.timeout)
        except Exception as e:
            # Volontairement large : kombu remonte OperationalError, redis-py
            # AuthenticationError, et une sonde ne doit jamais lever.
            return Health(
                name="broker",
                extras={"error": str(e)},
                version=celery.__version__,
                up_time=self.up_time,
                status=HealtStatus.UNHEALTHY.value,
            )
        return Health(
            name="broker",
            version=celery.__version__,
            up_time=self.up_time,
            status=HealtStatus.HEALTHY.value,
        )
