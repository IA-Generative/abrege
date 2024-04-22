from fastapi import FastAPI
import os, sys, logging, random, asyncio, uvicorn, time
from pathlib import Path

logger = logging.getLogger()

with Path('./README.md').open() as f: description = f.readline()

app = FastAPI(
    title="abrege",
    description=description,
    version="0.0.1",
)


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return



if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
