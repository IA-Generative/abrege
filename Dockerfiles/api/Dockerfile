FROM python:3.11.9-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libmagic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
ENV UV_CACHE_DIR=/app/.cache
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN uv sync --no-cache --group abrege-api

COPY api /app/api
COPY src/ /app/src
ENV PYTHONPATH=/app
CMD [ "uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000"]

FROM builder AS test
WORKDIR /app
RUN uv sync --no-cache --group test --group abrege-api
COPY tests tests
CMD [ "uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
