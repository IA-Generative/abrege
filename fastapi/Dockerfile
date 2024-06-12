#######################
# Step 1: Base target #
#######################
FROM python:3.11.9-slim-bookworm as base

RUN apt-get update \
    && apt-get install build-essential -y \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1


# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip install poetry

################################
# Step 2: "development" target #
################################
FROM base as dev

WORKDIR /app
# Copy everything for developpement purpose
COPY . .

WORKDIR /app/fastapi

RUN poetry lock && poetry install --with dev

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