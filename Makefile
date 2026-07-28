.PHONY: help up down build logs db-migrate db-shell redis-cli lint test

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker-compose up -d

build: ## Build all images
	docker-compose build

down: ## Stop all services
	docker-compose down

logs: ## Follow logs from all services
	docker-compose logs -f

logs-backend: ## Follow backend logs only
	docker-compose logs -f backend

logs-alloy: ## Follow Alloy log shipper
	docker-compose logs -f alloy

db-migrate: ## Run Flask database migrations
	docker-compose exec backend flask db upgrade

db-shell: ## Open psql shell
	docker-compose exec postgres psql -U $${POSTGRES_USER:-snip} -d $${POSTGRES_DB:-urlshortener}

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

lint: ## Run linters (Python + JS)
	docker-compose run --rm backend sh -c "pip install flake8 black isort --quiet && flake8 src/ && black --check src/ && isort --check src/"
	docker-compose run --rm frontend npm run lint

test: ## Run backend tests
	docker-compose run --rm \
		-e DATABASE_URL=sqlite:///:memory: \
		-e SECRET_KEY=test \
		-e JWT_SECRET_KEY=test \
		-e REDIS_URL=redis://redis:6379/0 \
		-e OTEL_ENABLED=false \
		backend python -m pytest

shell-backend: ## Shell into backend container
	docker-compose exec backend sh

health: ## Check service health
	@curl -s http://localhost:5000/health | python3 -m json.tool
	@curl -s http://localhost/health
