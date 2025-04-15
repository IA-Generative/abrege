FROM python:3.11.9-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV NLTK_DATA /app/.cache/nltk_data

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
ENV UV_CACHE_DIR=/app/.cache
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
ENV AUTO_DOWNLOAD_NLTK=false

RUN uv sync --no-cache --group abrege-api
RUN uv run python -m nltk.downloader -d /app/.cache/nltk_data averaged_perceptron_tagger_eng punkt_tab

COPY api /app/api
ENV PYTHONPATH=PYTHONPATH:/app/api
CMD [ "uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000" ]
