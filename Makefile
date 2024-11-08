SHELL = /bin/bash

export APP = abrege
export TAG = vO.0.1
export CURRENT_PATH := $(shell pwd)

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

shell:
	$(COMPOSE) exec -it fastapi bash -c "/bin/bash"
#############
#  General  #
#############

dev: exec-dev

prod: exec-prod

down: stop-dev stop-prod