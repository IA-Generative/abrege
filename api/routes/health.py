from fastapi import APIRouter
from typing import Tuple, Union
from api.schemas.health import Health, HealthError
from api import __version__, __name__
import datetime
import requests

from .summarize import client
from ..clients import client_marker

from api.config.paddle import Settings

settings = Settings()


router = APIRouter(tags=["Health"])
up_time = datetime.datetime.now().isoformat()


def get_marker_api_health() -> Union[Health, HealthError]:
    service_name = "marker_api"
    try:
        health_marker = client_marker.check_health()
        health = Health(name=service_name, version="unknow", up_time=up_time,
                        extras=health_marker.model_dump(), status="healthy")
        return health
    except Exception as e:
        error = HealthError(name=service_name, error=str(e), code_status=500)
        return error


def get_llm_health() -> Union[Health, HealthError]:
    service_name = "llm"
    try:
        dependencies = []
        for model in client.models.list():
            health = Health(name=model.id, version=client._version,
                            up_time=up_time, status="healthy")
            dependencies.append(health)
        return Health(name=service_name, version=client._version, up_time=up_time, status="healthy", dependencies=dependencies)
    except Exception as e:
        error = HealthError(name=service_name, error=str(e), code_status=500)
        return error


def get_paddle_ocr_health() -> Union[Health, HealthError]:
    service_name = "PADDLE_OCR"
    res = requests.get(
        url=settings.PADDLE_OCR_URL,
    )
    if res.status_code == 200:
        health = Health(
            name=service_name,
            version="",
            up_time=up_time,
        )
        return health
    else:
        error = HealthError(name=service_name, error="", code_status=500)

        return error


@router.get("/", status_code=200, response_model=Health)
async def healthcheck():
    dependencies = []
    status = "healthy"
    health_llm = get_llm_health()
    dependencies.append(health_llm)
    if not isinstance(health_llm, Health):
        status = "unhealthy"
    health_paddle_api = get_paddle_ocr_health()
    if not isinstance(health_paddle_api, Health):
        status = "unhealthy"
    health_marker_api = get_marker_api_health()
    dependencies.append(health_marker_api)
    if not isinstance(health_marker_api, Health):
        status = "unhealthy"

    return Health(
        name=__name__, version=__version__, up_time=datetime.datetime.now().isoformat(), extras={}, status=status, dependencies=dependencies
    )
