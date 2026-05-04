from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router
from api.routes.summarize import router as summarize_router
from api.routes.document_summary import doc_router
from api.routes.task import router as task_router
from src import __version__, __name__ as name
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title=name,
    description="",
    version=__version__,
)
Instrumentator().instrument(app).expose(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["Surrogate-Control"] = "no-store"
        return response


app.add_middleware(NoCacheMiddleware)

app.include_router(health_router, prefix="/api")
app.include_router(summarize_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(doc_router, prefix="/api")
