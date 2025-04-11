import logging
import os
import re
import traceback
import asyncio

import uvicorn
from __init__ import __name__ as name
from __init__ import __version__
from routes.health import router as health_router
from routes.summarize import deprecated_router
from routes.summarize import router as summarize_router

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
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

class CatchExceptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await asyncio.wait_for(call_next(request), timeout=40)
            return response
        except asyncio.TimeoutError:
            return JSONResponse(status_code=504, content={"detail": "L'application ne répond pas"}) # Il ne faut pas utiliser de HTTPException ici
        except Exception as e:
            #logging.error(f"Erreur capturée au niveau du middleware : {e}\n{traceback.format_exc()}\n--------")
            return JSONResponse(status_code=500, content={"detail": "Une erreur interne est survenue."}) # Il ne faut pas utiliser de HTTPException ici

app.add_middleware(CatchExceptionsMiddleware) # CatchExceptionsMiddleware doit être ajouté APRES CORSMiddleware
app.include_router(health_router, prefix="/health")
app.include_router(summarize_router, prefix="/api")
app.include_router(deprecated_router, prefix="")


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=8000, host="0.0.0.0")
