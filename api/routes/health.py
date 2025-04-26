from fastapi import APIRouter
from typing import Union
from api.schemas.health import Health, HealthError
from api import __version__, __name__
import datetime
import requests

from api.config.paddle import Settings
from api.utils.logger import logger_abrege

settings = Settings()


router = APIRouter(tags=["Health"])
up_time = datetime.datetime.now().isoformat()


def get_paddle_ocr_health() -> Union[Health, HealthError]:
    service_name = "PADDLE_OCR"
    try:
        res = requests.get(
            url=settings.PADDLE_OCR_URL,
        )
        if res.status_code == 200:
            logger_abrege.debug("Check Paddle")
            health = Health(
                name=service_name,
                version="",
                up_time=up_time,
            )
            return health
        else:
            logger_abrege.error("Paddle not available")
            error = HealthError(
                name=service_name,
                error="Paddle not available",
                code_status=res.status_code,
            )

            return error
    except Exception as e:
        logger_abrege.error("Paddle not available")
        return HealthError(name=service_name, error=f"{str(e)}", code_status=500)


@router.get("/", status_code=200, response_model=Health)
async def healthcheck():
    dependencies = []
    status = "healthy"
    health_paddle_api = get_paddle_ocr_health()
    if not isinstance(health_paddle_api, Health):
        status = "unhealthy"
    dependencies.append(health_paddle_api)
    logger_abrege.debug("Health avalaible")
    return Health(
        name=__name__,
        version=__version__,
        up_time=up_time,
        extras={},
        status=status,
        dependencies=dependencies,
    )
