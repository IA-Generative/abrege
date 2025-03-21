#######################
# Step 1: Base target #
#######################
FROM python:3.11.9-slim as base
WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
RUN uv sync --no-cache

################################
# Step 2: "development" target #
################################
FROM base as dev

WORKDIR /app
# Copy everything for developpement purpose
COPY . .

WORKDIR /app/fastapi

RUN poetry lock && poetry install --with dev
# Sometimes src/abrege seems to be not installed in editable
WORKDIR /app/src
RUN pip install -e .
WORKDIR /app/fastapi

CMD [ "bash", "run.sh" ]

################################
# Step 3: "production" target  #
################################
FROM base as prod

WORKDIR /app/src

COPY ./src /app/src/

WORKDIR /app/fastapi

COPY ./fastapi /app/fastapi/

RUN poetry lock && poetry install

CMD ["bash", "run.sh"]