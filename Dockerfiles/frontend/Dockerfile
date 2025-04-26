FROM python:3.11.9-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

EXPOSE $FRONTEND_PORT
WORKDIR /app

RUN uv sync --group frontend

COPY frontend /app/

HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health

CMD ["uv", "run", "streamlit", "run", "/app/app/main.py", "--server.port=8080", "--server.address=0.0.0.0"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]
