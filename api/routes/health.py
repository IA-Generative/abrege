from fastapi import APIRouter
from api.schemas.health import Health, HealthError
from api import __version__, __name__
import datetime
import requests

from .summarize import client

from api.config.paddle import Settings

settings = Settings()


def get_status_paddle_ocr():
    res = requests.get(
        url=settings.PADDLE_OCR_URL,

    )

    return res.status_code == 200


router = APIRouter(tags=['Health'])


@router.get("/", status_code=200, response_model=Health)
async def healthcheck():
    dependencies = []
    for model in client.models.list():
        health = Health(name=model.id, version=client._version,
                        up_time=datetime.datetime.now().isoformat(), status="healthy")
        dependencies.append(health)

    status = get_status_paddle_ocr()
    if status:
        health = Health(name="PADDLE_OCR", version="",
                        up_time=datetime.datetime.now().isoformat(),)

        dependencies.append(health)
    else:
        error = HealthError(name='PADDLE_OCR', error="", code_status=500)
        dependencies.append(error)
    return Health(
        name=__name__,
        version=__version__,
        up_time=datetime.datetime.now().isoformat(),
        extras={},
        status="healthy",
        dependencies=dependencies
    )
