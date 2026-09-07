#######################
# Step 1: Base target #
#######################
FROM python:3.11.9-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libmagic1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/server/pyproject.toml /app/pyproject.toml
COPY apps/server/uv.lock /app/uv.lock
ENV UV_CACHE_DIR=/app/.cache
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN uv sync --no-cache --group abrege-api --group migration

COPY apps/server/api /app/api
COPY apps/server/src/ /app/src
COPY apps/server/config /app/config

COPY apps/server/migration /app/migration
COPY apps/server/src/ /app/src/
COPY apps/server/migration/alembic.ini /app/

ENV PYTHONPATH=PYTHONPATH:/app
ENV PATH=$PATH:/app/.venv/bin/

# OpenShift's restricted-v2 SCC ignores the image's USER and runs the container as an
# arbitrary UID from the namespace's range, always with GID 0. Owning the tree by group
# root and mirroring the owner bits onto the group is what lets one image work both as
# 10001 on the current cluster and as that arbitrary UID later.
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home --home-dir /app --shell /usr/sbin/nologin appuser \
    && chown -R 10001:0 /app \
    && chmod -R g=u /app

# Numeric, not `appuser`: with `runAsNonRoot: true` and no explicit `runAsUser`, the
# kubelet cannot resolve a named user and refuses to start the container.
USER 10001:10001

CMD [ "uv", "run", "--no-cache", "python", "/app/api/main.py" ]
################################
# Step 2: "development" target #
################################
FROM base AS dev
WORKDIR /app
RUN uv sync --no-cache --group test --group abrege-api --group migration
COPY --chown=10001:0 apps/server/tests tests
CMD [ "uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload", "--log-config", "config/uvicorn_logging.yaml"]
