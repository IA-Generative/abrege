FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_CACHE_DIR=/app/.cache
WORKDIR /app
COPY alembic.ini /app/
COPY migration /app/migration
COPY src/ /app/src/
COPY pyproject.toml uv.lock ./

RUN uv sync --no-cache --group migration

ENV PATH=$PATH:/app/.venv/bin/
ENV PYTHONPATH=/app
