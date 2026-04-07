.PHONY: help up down infra backend-dev frontend-dev test backend-test scrapers-test frontend-test lint build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ──────────────────────────────────────────────────────────────────

up: ## Start all services
	docker compose up --build -d

down: ## Stop all services
	docker compose down

infra: ## Start only infrastructure (db + redis)
	docker compose up -d db redis

logs: ## Tail logs for all services
	docker compose logs -f

build: ## Build all Docker images
	docker compose build

# ── Backend ─────────────────────────────────────────────────────────────────

backend-dev: ## Run backend dev server (requires local Python env)
	cd backend && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

backend-test: ## Run backend tests
	cd backend && poetry run pytest src/tests/ -v

backend-lint: ## Lint backend code
	cd backend && poetry run ruff check src/ && poetry run ruff format --check src/

backend-shell: ## Open a shell in the backend container
	docker compose exec web bash

# ── Scrapers ────────────────────────────────────────────────────────────────

scrapers-test: ## Run scraper tests
	cd scrapers && poetry run pytest src/tests/ -v

scrapers-lint: ## Lint scraper code
	cd scrapers && poetry run ruff check src/ && poetry run ruff format --check src/

# ── Frontend ────────────────────────────────────────────────────────────────

frontend-dev: ## Run frontend dev server
	cd frontend && npm run dev

frontend-test: ## Run frontend tests
	cd frontend && npm run test

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

frontend-build: ## Build frontend for production
	cd frontend && npm run build

# ── All ─────────────────────────────────────────────────────────────────────

test: backend-test scrapers-test frontend-test ## Run all tests

lint: backend-lint scrapers-lint frontend-lint ## Lint all services
