FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY alembic.ini /app/
COPY migration /app/migration
COPY src/ /app/src/
COPY pyproject.toml uv.lock ./

RUN uv sync --no-cache --group abrege-service --group migration

# Ajout du répertoire des outils uv au PATH


ENV PYTHONPATH=/app
