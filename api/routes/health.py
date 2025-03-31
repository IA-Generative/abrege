from fastapi import APIRouter
from schemas.health import Health
from __init__ import __version__, __name__
import datetime


router = APIRouter()


@router.get("/", status_code=200, response_model=Health)
async def healthcheck():
    return Health(
        name=__name__,
        version=__version__,
        up_time=datetime.datetime.now().isoformat(),
        extras={},
        status="healthy",
    )
