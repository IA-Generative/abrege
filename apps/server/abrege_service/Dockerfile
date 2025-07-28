FROM python:3.11-slim AS builder

# Copier les binaires uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=pandoc/minimal:2.19.2 /pandoc /usr/bin/pandoc

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
        poppler-utils \
        libatomic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV UV_CACHE_DIR=/app/.cache
ENV CACHE_FOLDER=/app/.cache

COPY pyproject.toml uv.lock ./

RUN uv sync --no-cache --group abrege-service

RUN mkdir -p /app/data/models && \
    curl -L -o vosk-model-small-fr-0.22.zip https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip && \
    unzip vosk-model-small-fr-0.22.zip -d /app/data/models && \
    rm vosk-model-small-fr-0.22.zip

COPY apps/server/abrege_service /app/abrege_service
COPY apps/server/src /app/src

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "abrege_service/main.py"]


FROM builder AS test
WORKDIR /app
RUN uv sync --no-cache --group test --group abrege-service
COPY apps/server/tests tests
CMD ["uv", "run", "abrege_service/main.py"]
