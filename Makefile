PYTHONPATH=$(PWD)

.PHONY: install-uv install-local linter test-bakend \
        up down build \
        upgrade-db upgrade-revision help

.DEFAULT_GOAL := help

help:
	@echo "Usage: make <command>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

install: install-uv ## Installation de l'environnement pour du développement local (gestionnaire de dépendances)
	@if [ ! -d "apps/server/.venv" ]; then \
		echo "Synchronisation des dépendances..."; \
		cd apps/server && uv sync --group test --group abrege-api --group abrege-service; \
	else \
		echo "Dépendances déjà synchronisées (suppose .venv existant)"; \
	fi

install-uv:
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "uv non trouvé, installation..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "uv déjà installé"; \
	fi

install-linux:
	sudo apt update && sudo apt install -y poppler-utils ffmpeg

install-mac:
	brew install poppler ffmpeg

install-local: ## Installation des dépendances systèmes
	ifeq ($(shell uname), Linux)
		@$(MAKE) install-linux
	else ifeq ($(shell uname), Darwin)
		@$(MAKE) install-mac
	else
		@echo "Installation automatique non supportée sur cette plateforme"
	endif

lint: ## Lint le code du dépôt
	cd apps/server && \
		uv run ruff check --exclude '**/*.ipynb' . && \
		uv run ruff check .

lint-sdk: ## Lint le code du dépôt
	cd sdk/ && \
		uv run ruff check --exclude '**/*.ipynb' . && \
		uv run ruff check .

lint-fix: ## Lint et correction automatique du code backend
	cd apps/server && \
		uv run ruff check --exclude '**/*.ipynb' . --fix && \
		uv run ruff format .

up: ## Lance l'environnement de développement en conteneurs
	docker compose up -d

setup-frontend: clean-front ## Prépare le frontend pour le développement
	pnpm install
	cd apps/client && \
		pnpm install && \
		pnpm update

up-frontend: setup-frontend ## Lance l'environnement de développement en conteneurs pour le frontend
	docker compose -f docker-compose.frontend.yml up -d

down: ## Eteint l'environnement de développement en conteneurs
	docker compose down || true

clean: ## Nettoyage du dépôt
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	rm *.db

clean-front: ## Nettoyage du frontend
	docker compose -f docker-compose.frontend.yml down || true
	rm -rf node_modules
	cd apps/client && \
 		rm -rf node_modules && \
		rm -rf dist


########################### DOCKER BUILD ###########################

build-abrege-api:
	docker compose build abrege_api

build-abrege-service:
	docker compose build abrege_service


build: build-abrege-api build-abrege-service ## Lance la construction de toutes les images Docker


####################################################################

down-services:
	docker compose down --remove-orphans || true

init-db:
	docker compose up -d --remove-orphans redis db minio
	@echo "Attente de la base de données..."
	@docker compose exec db sh -c 'until pg_isready -h localhost -p 5432; do sleep 1; done'
	docker compose run --rm migration uv run alembic upgrade head

upgrade-revision: ## Crée une nouvelle révision de base de données
	@read -p "Message de révision : " msg; \
	docker compose run --rm migration uv run alembic revision --autogenerate -m "$$msg"


upgrade-db: ## Met à jour la base de données à la dernière révision
	docker compose run --rm migration uv run alembic upgrade head

wait-api:
	@echo "Attente de l'API..."
	@until docker compose exec abrege_api python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" > /dev/null 2>&1; do sleep 2; done
	@echo "API prête."

test-src: init-db ## Tests sur les sources (repository)
	docker compose up -d --remove-orphans abrege_api
	@$(MAKE) wait-api
	docker compose exec abrege_api uv run pytest -s --cov=./src --cov-report=term-missing tests/src/repository -ra -v --maxfail=0
	@$(MAKE) down-services

test-abrege-api: init-db ## Tests de l'API
	docker compose up -d --remove-orphans abrege_api
	@$(MAKE) wait-api
	docker compose exec abrege_api uv run pytest -s --cov=./api --cov-report=term-missing tests/api/ -ra -v --maxfail=0
	@$(MAKE) down-services

test-abrege-service: init-db ## Tests du service abrégé
	docker compose up -d --remove-orphans abrege_api
	@$(MAKE) wait-api
	docker compose run --rm abrege_service uv run pytest -s --cov=./abrege_service/ --cov-report=term-missing tests/abrege_service/ -ra -v --maxfail=1
	@$(MAKE) down-services


test-sdk-python: ## Tests du SDK Python
	cd sdk && \
		uv run pytest -s --cov=./abrege_sdk --cov-report=term-missing tests/ -ra -v --maxfail=0