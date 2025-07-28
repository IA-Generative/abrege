FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_CACHE_DIR=/app/.cache
WORKDIR /app
COPY alembic.ini /app/
COPY apps/server/migration /app/migration
COPY apps/server/src/ /app/src/
COPY apps/server/pyproject.toml apps/server/uv.lock ./
COPY apps/server/migration/alembic.ini /app/

RUN uv sync --no-cache --group migration

ENV PATH=$PATH:/app/.venv/bin/
ENV PYTHONPATH=/app
