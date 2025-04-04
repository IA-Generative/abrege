SHELL = /bin/bash

export APP = abrege
export LATEST_TAG := $(shell git describe --tags --abbrev=0 || echo "latest")
export CURRENT_PATH := $(shell pwd)
export IMAGE_API_BASE_NAME = ia-generative/abrege
export IMAGE_API_OLD_NAME = ia-generative/old-abrege
export IMAGE_STREAMLIT_BASE_NAME = ia-generative/streamlit-abrege

export COMPOSE ?= docker compose
export DC_UP_ARGS = #--build --force-recreate
export DC_BUILD_ARGS = #--no-cache

#BACKEND
export BACKEND_PORT = 8000

# NETWORK
export DC_NETWORK_OPT = --opt com.docker.network.driver.mtu=1450 # In RIE network
export DC_NETWORK = ia-foule


network:
	docker network create ${DC_NETWORK_OPT} ${DC_NETWORK} 2> /dev/null; true


build-dev: network
	$(COMPOSE) -f docker-compose.yaml -f docker-compose-dev.yaml build $(DC_BUILD_ARGS)

exec-dev:
	$(COMPOSE) -f docker-compose-dev.yaml up $(DC_UP_ARGS)
stop-dev:
	$(COMPOSE) -f docker-compose-dev.yaml down

test-dev:
	$(COMPOSE) exec -i fastapi bash -c "cd ../ && pytest --runslow"

build-prod: network
	$(COMPOSE) -f docker-compose.yaml build $(DC_BUILD_ARGS)
	
exec-prod:
	$(COMPOSE) -f docker-compose.yaml up $(DC_UP_ARGS)

stop-prod:
	$(COMPOSE) -f docker-compose.yaml down

test-prod:
	$(COMPOSE) cp ./tests fastapi:/app
	$(COMPOSE) cp ./pyproject.toml fastapi:/app
	$(COMPOSE) exec -i fastapi bash -c "cd ../ && pytest --runslow"
	$(COMPOSE) exec -i fastapi bash -c "cd ../ && rm -r tests && rm pyproject.toml"


docker-login:
	@echo "Connexion à la registry Docker $(DOCKER_REGISTRY)..."
	docker login "$(DOCKER_REGISTRY)" -u "$(DOCKER_USERNAME)" -p "$(DOCKER_PASSWORD)"
	@echo "Connexion réussie !"

##################### abrege-api #####################
docker-build-api:
	@echo "Building $(IMAGE_API_BASE_NAME) image..."
	docker build -t $(DOCKER_REGISTRY)/$(IMAGE_API_BASE_NAME):$(LATEST_TAG) -f Dockerfiles/api/Dockerfile .

docker-push-api: docker-login docker-build-api
	@echo "Push de l'image $(DOCKER_REGISTRY)/$(IMAGE_API_BASE_NAME):$(LATEST_TAG)..."
	docker push "$(DOCKER_REGISTRY)/$(IMAGE_API_BASE_NAME):$(LATEST_TAG)"
	@echo "Image poussée avec succès : $(DOCKER_REGISTRY)/$(IMAGE_API_BASE_NAME):$(LATEST_TAG)"

##################### end abrege-api #####################

##################### abrege-streamlit #####################
docker-build-streamlit:
	@echo "Building $(IMAGE_STREAMLIT_BASE_NAME) image..."
	docker build -t $(DOCKER_REGISTRY)/$(IMAGE_STREAMLIT_BASE_NAME):$(LATEST_TAG) -f Dockerfiles/frontend/Dockerfile .

docker-push-streamlit: docker-login docker-build-streamlit
	@echo "Push de l'image $(DOCKER_REGISTRY)/$(IMAGE_STREAMLIT_BASE_NAME):$(LATEST_TAG)..."
	docker push "$(DOCKER_REGISTRY)/$(IMAGE_STREAMLIT_BASE_NAME):$(LATEST_TAG)"
	@echo "Image poussée avec succès : $(DOCKER_REGISTRY)/$(IMAGE_STREAMLIT_BASE_NAME):$(LATEST_TAG)"

##################### end abrege-frontend #####################


##################### abrege-fastapi-old #####################
docker-build-fastapi-old:
	@echo "Building $(IMAGE_API_OLD_NAME) image..."
	docker build -t $(DOCKER_REGISTRY)/$(IMAGE_API_OLD_NAME):$(LATEST_TAG) -f fastapi/Dockerfile .

docker-push-fastapi-old: docker-login docker-build-fastapi-old
	@echo "Push de l'image $(DOCKER_REGISTRY)/$(IMAGE_API_OLD_NAME):$(LATEST_TAG)..."
	docker push "$(DOCKER_REGISTRY)/$(IMAGE_API_OLD_NAME):$(LATEST_TAG)"
	@echo "Image poussée avec succès : $(DOCKER_REGISTRY)/$(IMAGE_API_OLD_NAME):$(LATEST_TAG)"

##################### end abrege-fastapi-old #####################

shell:
	$(COMPOSE) exec -it fastapi bash -c "/bin/bash"



#############
#  General  #
#############

dev: exec-dev

prod: exec-prod

down: stop-dev stop-prod

runapi:
	@export $(shell grep -v '^#' .env | xargs) && uv run python api/main.py