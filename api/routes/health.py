from fastapi import APIRouter
import datetime

from src.utils.logger import logger_abrege
from src.schemas.health import Health
from src import __version__, __name__


router = APIRouter(tags=["Health"])
up_time = datetime.datetime.now().isoformat()


@router.get("/", status_code=200, response_model=Health)
async def healthcheck():
    dependencies = []
    status = "healthy"
    logger_abrege.debug("Health avalaible")
    return Health(
        name=__name__,
        version=__version__,
        up_time=up_time,
        extras={},
        status=status,
        dependencies=dependencies,
    )
