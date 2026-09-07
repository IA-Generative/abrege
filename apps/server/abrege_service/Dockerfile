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
        libicu-dev \
        libatomic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV UV_CACHE_DIR=/app/.cache
ENV CACHE_FOLDER=/app/.cache

COPY apps/server/pyproject.toml apps/server/uv.lock ./

RUN uv sync --no-cache --group abrege-service

RUN mkdir -p /app/data/models && \
    curl -L -o vosk-model-small-fr-0.22.zip https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip && \
    unzip vosk-model-small-fr-0.22.zip -d /app/data/models && \
    rm vosk-model-small-fr-0.22.zip

COPY apps/server/abrege_service /app/abrege_service
COPY apps/server/src /app/src
COPY apps/server/config /app/config

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# OpenShift's restricted-v2 SCC ignores the image's USER and runs the container as an
# arbitrary UID from the namespace's range, always with GID 0. Owning the tree by group
# root and mirroring the owner bits onto the group is what lets one image work both as
# 10001 on the current cluster and as that arbitrary UID later. Covers /app/data/models
# (vosk model downloaded above) and /app/.cache (CACHE_FOLDER, written to at runtime).
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home --home-dir /app --shell /usr/sbin/nologin appuser \
    && chown -R 10001:0 /app \
    && chmod -R g=u /app

# Numeric, not `appuser`: with `runAsNonRoot: true` and no explicit `runAsUser`, the
# kubelet cannot resolve a named user and refuses to start the container.
USER 10001:10001

CMD ["uv", "run", "abrege_service/main.py"]


FROM builder AS test
WORKDIR /app
RUN uv sync --no-cache --group test --group abrege-service
COPY --chown=10001:0 apps/server/tests tests
CMD ["uv", "run", "abrege_service/main.py"]
