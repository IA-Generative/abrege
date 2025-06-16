from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router
from api.routes.summarize import router as summarize_router
from api.routes.document_summary import doc_router
from api.routes.task import router as task_router
from src import __version__, __name__ as name


app = FastAPI(
    title=name,
    description="",
    version=__version__,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(summarize_router, prefix="/api")

app.include_router(health_router)
app.include_router(summarize_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(doc_router, prefix="/api")
