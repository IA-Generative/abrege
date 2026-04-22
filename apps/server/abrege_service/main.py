import abrege_service.tasks.abrege  # noqa: F401
import abrege_service.tasks.merge  # noqa: F401
import abrege_service.tasks.chunk_task  # noqa: F401
from src.clients import celery_app

if __name__ == "__main__":
    celery_app.start()
