FROM python:3.11.9-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE $FRONTEND_PORT
WORKDIR /app

RUN uv sync --no-cache --group frontend

COPY frontend /app/

CMD ["bash", "run.sh"]