import re
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .logger import logger_abrege


def set_cors(app: FastAPI, origins=("http://localhost", "http://localhost:8000")):
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
    return app
