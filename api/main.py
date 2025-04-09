import logging
import os
import re
import traceback
import sys

import uvicorn
from __init__ import __name__ as name
from __init__ import __version__


logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

from routes.health import router as health_router
from routes.summarize import deprecated_router
from routes.summarize import router as summarize_router

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

origins = ("http://localhost", "http://localhost:8000")

app = FastAPI(
    title=name,
    description="",
    version=__version__,
)

if "CORS_REGEXP" in os.environ:
    origin_regex = os.environ["CORS_REGEXP"]

    try:
        re.compile(origin_regex)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=origin_regex,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logging.warning(f"allow_origin_regex={origin_regex}")
    except re.error:
        logging.error(f"CORS_REGEXP = {origin_regex} is not a valid regex")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
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

        return JSONResponse(status_code=500, content={"detail": "Une erreur interne est survenue."})


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=8000, host="0.0.0.0")
