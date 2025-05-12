import re
import os
import asyncio
import traceback
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.utils.logger import logger_abrege


class CatchExceptionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await asyncio.wait_for(call_next(request), timeout=40)
            return response
        except asyncio.TimeoutError as e:
            logger_abrege.error(f"{e}")
            return JSONResponse(status_code=504, content={"detail": "L'application ne répond pas"})
            # Il ne faut pas utiliser de HTTPException ici
        except Exception as e:
            error_message = f"Erreur capturée au niveau du middleware : {e}\n{traceback.format_exc()}\n--------"
            logger_abrege.error(error_message)
            return JSONResponse(
                status_code=500, content={"detail": "Une erreur interne est survenue."}
            )  # Il ne faut pas utiliser de HTTPException ici


def set_cors(app: FastAPI, origins=("http://localhost", "http://localhost:5000")):
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
            logger_abrege.warning(f"allow_origin_regex={origin_regex}")
        except re.error:
            logger_abrege.error(f"CORS_REGEXP = {origin_regex} is not a valid regex")
            app.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
    # app.add_middleware(CatchExceptionsMiddleware)
    # CatchExceptionsMiddleware doit être ajouté APRES CORSMiddlewar
    return app
