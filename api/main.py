from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.health import router as health_router
from routes.summarize import deprecated_router
from routes.summarize import router as summarize_router
from routes.summarize import deprecated_router
from __init__ import __version__, __name__ as name


origins = (
    "https://sie.numerique-interieur.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:8501",
)

origin_regex = "https://.*\.cloud-pi-native\.com"
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


app.include_router(health_router, prefix="/health")
app.include_router(summarize_router, prefix="/api")
app.include_router(deprecated_router, prefix="")


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logging.error(f"{e}\n{traceback.format_exc()}")

        return JSONResponse(
            status_code=500, content={"detail": "Une erreur interne est survenue."}
        )


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=8000, host="0.0.0.0")
app.include_router(health_router)
app.include_router(summarize_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(doc_router, prefix="/api")
