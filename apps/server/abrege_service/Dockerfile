FROM python:3.11-slim AS builder

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
        libsm6 \
        libxext6 \
        poppler-utils \
        libicu-dev \
        libatomic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV UV_CACHE_DIR=/app/.cache
ENV CACHE_FOLDER=/app/.cache

# OpenShift's restricted-v2 SCC ignores the image's USER and runs the container as an
# arbitrary UID from the namespace's range, always with GID 0. Creating the user with
# GID 0 as its *primary* group - before installing anything - means every file created
# from here on (venv, source, cache) already gets group 0 for free: no `chown -R` needed
# at the end, which used to double the size of every layer it touched (it rewrites every
# file's metadata, so Docker stores a full extra copy of the tree as a new layer).
RUN useradd --uid 10001 --gid 0 --no-create-home --home-dir /app --shell /usr/sbin/nologin appuser \
    && chown 10001:0 /app \
    && chmod g=u /app

COPY --chown=10001:0 apps/server/pyproject.toml apps/server/uv.lock ./

# Numeric, not `appuser`: with `runAsNonRoot: true` and no explicit `runAsUser`, the
# kubelet cannot resolve a named user and refuses to start the container. GID 0 so
# everything this user creates from here on matches the primary group set above.
USER 10001:0

RUN uv sync --no-cache --group abrege-service

COPY --chown=10001:0 apps/server/abrege_service /app/abrege_service
COPY --chown=10001:0 apps/server/src /app/src
COPY --chown=10001:0 apps/server/config /app/config

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "abrege_service/main.py"]


FROM builder AS test
WORKDIR /app
RUN uv sync --no-cache --group test --group abrege-service
COPY --chown=10001:0 apps/server/tests tests
CMD ["uv", "run", "abrege_service/main.py"]
