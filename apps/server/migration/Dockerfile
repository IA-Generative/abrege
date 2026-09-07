FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_CACHE_DIR=/app/.cache
WORKDIR /app
COPY apps/server/migration/alembic.ini /app/
COPY apps/server/migration /app/migration
COPY apps/server/src/ /app/src/
COPY apps/server/pyproject.toml apps/server/uv.lock ./
COPY apps/server/migration/alembic.ini /app/

RUN uv sync --no-cache --group migration

ENV PATH=$PATH:/app/.venv/bin/
ENV PYTHONPATH=/app

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
