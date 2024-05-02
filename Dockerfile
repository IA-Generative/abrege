# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim


RUN apt-get update  \
    && apt-get install build-essential -y \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*
    
EXPOSE $BACKEND_PORT

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1


# Install app
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . .

# Install abrege package
WORKDIR /app/abrege
RUN pip install -r requirements.txt
RUN  pip install -e .
WORKDIR /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app && mkdir -p /data/feedbacks && chown -R appuser /data/feedbacks
# USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]