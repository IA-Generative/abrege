from fastapi import APIRouter
from fastapi.responses import JSONResponse
import datetime

from src.utils.logger import logger_abrege
from src.schemas.health import Health, HealtStatus
from src import __version__, __name__


router = APIRouter(tags=["Health"])
up_time = datetime.datetime.now().isoformat()


@router.get("/", response_model=Health)
async def healthcheck():
    dependencies = []
    status = HealtStatus.HEALTHY.value
    status_code = 200
    # status_task_table, error = task_table.health_check()
    dependencies.append(Health(name="task-table", version=__version__, up_time=up_time, status=status))
    logger_abrege.debug("Health avalaible")
    global_health = Health(
        name=__name__,
        version=__version__,
        up_time=up_time,
        extras={},
        status=status,
        dependencies=dependencies,
    )
    logger_abrege.debug(global_health.model_dump())
    return JSONResponse(content=global_health.model_dump(), status_code=status_code)
