import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from routes.health import router as health_router
from routes.summarize import router as summarize_router
from routes.summarize import deprecated_router
from __init__ import __version__, __name__ as name


#origins = ("https://sie.numerique-interieur.com", "http://localhost", "http://localhost:8080", "http://localhost:8501")
origins = ['*']

origin_regex = r"https:\/\/.*\.(?:cloud-pi-native|numerique-interieur)\.com"

app = FastAPI(
    title=name,
    description="",
    version=__version__,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    #allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router, prefix="/health")
app.include_router(summarize_router, prefix="/api")
app.include_router(deprecated_router, prefix="")

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=8000, host="0.0.0.0")
