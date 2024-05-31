FROM python:3.11.9-slim-bookworm

RUN apt-get update \
    && apt-get install build-essential -y \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

EXPOSE $FRONTEND_PORT

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./frontend .

ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip install poetry
RUN poetry lock && poetry install

CMD ["bash", "run.sh"]