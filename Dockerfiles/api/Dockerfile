#######################
# Step 1: Base target #
#######################
FROM python:3.11.9-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
RUN uv sync --no-cache --group abrege-api

COPY api /app/api
ENV PYTHONPATH=PYTHONPATH:/app
CMD [ "uv", "run", "--no-cache", "python", "/app/api/main.py" ]
################################
# Step 2: "development" target #
################################
#FROM base AS dev
#WORKDIR /app
#RUN uv sync --no-cache --group tests
#COPY tests /app/tests
