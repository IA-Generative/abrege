from datetime import datetime

import redis
from redis.exceptions import RedisError

from src.schemas.health import Health, HealtStatus


class RedisConnector:
    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client
        self.up_time = datetime.now().isoformat()

    def get_health(self) -> Health:
        try:
            self.client.ping()
        except RedisError as e:
            return Health(
                name="redis",
                extras={"error": str(e)},
                version=redis.__version__,
                up_time=self.up_time,
                status=HealtStatus.UNHEALTHY.value,
            )
        return Health(
            name="redis",
            version=redis.__version__,
            up_time=self.up_time,
            status=HealtStatus.HEALTHY.value,
        )
