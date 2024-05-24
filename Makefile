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

dummy		    := $(shell touch .env)

#############
#  Network  #
#############

network:
	@docker network create ${DC_NETWORK_OPT} ${DC_NETWORK} 2> /dev/null; true

#############
#  Backend  #
#############


backend-build:
	@$(COMPOSE) -f docker-compose.yaml build $(DC_BUILD_ARGS)

backend-dev: network
	@echo "Listening on port: $(BACKEND_PORT)"
	$(COMPOSE) -f docker-compose.yaml -f docker-compose-dev.yaml up -d $(DC_UP_ARGS)


backend-exec:
	$(COMPOSE) -f docker-compose.yaml -f docker-compose-dev.yaml run -ti abrege bash

# backend-test:
# 	$(COMPOSE) -f docker-compose.yaml -f docker-compose-dev.yaml run --rm --name=${APP} abrege /bin/sh -c 'pip3 install pytest && pytest tests/ -s'
