FROM python:3.11-slim

# Copier les binaires uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Réduction des interactions lors de l'installation
ENV DEBIAN_FRONTEND=noninteractive

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        libmagic1 \
        ffmpeg \
        libsm6 \
        libxext6 \
        curl \
        unzip \
        poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV UV_CACHE_DIR=/app/.cache

COPY pyproject.toml uv.lock ./

RUN uv sync --no-cache --group abrege-service

COPY abrege_service /app/abrege_service
COPY src /app/src

RUN mkdir -p /app/abrege_service/data/models && \
    curl -L -o vosk-model-small-fr-0.22.zip https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip && \
    unzip vosk-model-small-fr-0.22.zip -d /app/abrege_service/data/models && \
    rm vosk-model-small-fr-0.22.zip

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "abrege_service/main.py"]
