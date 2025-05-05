from fastapi import FastAPI

from api.routes.health import router as health_router
from api.routes.summarize import router as summarize_router
from api.routes.document_summary import router as document_router
from api.routes.task import router as task_router
from src import __version__, __name__ as name
from api.utils.cors import set_cors


app = FastAPI(
    title=name,
    description="",
    version=__version__,
)


app = set_cors(app)


app.include_router(health_router, prefix="/health")
app.include_router(summarize_router, prefix="/api")
app.include_router(document_router, prefix="/api")
app.include_router(task_router, prefix="/api")
