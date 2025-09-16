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
		uv run ruff format --check .

lint-fix: ## Lint et correction automatique du code backend
	cd apps/server && \
		uv run ruff check --exclude '**/*.ipynb' . --fix && \
		uv run ruff format .

up: ## Lance l'environnement de développement en conteneurs
	docker compose up -d

setup-frontend: clean-front ## Prépare le frontend pour le développement
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
	docker compose up -d redis db minio migration
	sleep 2
	docker compose run migration uv run alembic upgrade head
	sleep 2

upgrade-revision: ## Crée une nouvelle révision de base de données
	@read -p "Message de révision : " msg; \
	docker compose run --rm migration uv run alembic revision --autogenerate -m "$$msg"

test-src: init-db
	docker compose up -d abrege_api
	docker compose exec abrege_api uv run pytest -s --cov=./src --cov-report=term-missing tests/src/ -ra -v --maxfail=0
	make down-services

test-abrege-api: init-db
	docker compose up -d abrege_api
	docker compose exec abrege_api uv run pytest -s --cov=./api --cov-report=term-missing tests/api/ -ra -v --maxfail=0
	make down-services

test-abrege-service: init-db
	docker compose run --rm test_runner
	make down-services
