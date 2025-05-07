FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

# Ajout du répertoire des outils uv au PATH
ENV PATH="/root/.local/bin:$PATH"

RUN uv tool install alembic


COPY alembic.ini /app/
COPY migration /app/migration
COPY src/ /app/src/

ENV PYTHONPATH=/app
