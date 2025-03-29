.PHONY: help build rebuild up up-d down logs shell restart clean migrate migrate-up migrate-down db-shell test test-cov

# Help command
help:
	@echo "PDF Extractor - Make commands"
	@echo ""
	@echo "Usage:"
	@echo "  make build     - Build the Docker image"
	@echo "  make rebuild   - Rebuild and restart the Docker container"
	@echo "  make up        - Start the Docker container in foreground mode"
	@echo "  make up-d      - Start the Docker container in detached mode"
	@echo "  make down      - Stop the Docker container"
	@echo "  make logs      - Show Docker container logs"
	@echo "  make shell     - Open a shell in the running container"
	@echo "  make restart   - Restart the Docker container"
	@echo "  make clean     - Remove Docker containers, images, and volumes"
	@echo "  make migrate   - Generate a new migration script"
	@echo "  make migrate-up - Apply migrations"
	@echo "  make migrate-down - Revert last migration"
	@echo "  make db-shell  - Open a PostgreSQL shell"
	@echo "  make test      - Run tests"
	@echo "  make test-cov  - Run tests with coverage report"
	@echo "  make help      - Show this help message"

# Docker commands
build:
	@echo "Building Docker image..."
	docker-compose build

rebuild:
	@echo "Rebuilding and restarting Docker containers..."
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "Containers rebuilt and restarted"

up:
	@echo "Starting Docker container in foreground..."
	docker-compose up

up-d:
	@echo "Starting Docker container in detached mode..."
	docker-compose up -d

down:
	@echo "Stopping Docker container..."
	docker-compose down

logs:
	@echo "Showing logs..."
	docker-compose logs -f

shell:
	@echo "Opening shell in container..."
	docker-compose exec pdf-extractor /bin/bash

restart:
	@echo "Restarting container..."
	docker-compose restart

clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker-compose rm -f

migrate:
	@echo "Generating new migration script..."
	docker-compose exec pdf-extractor alembic revision --autogenerate -m "$(message)"

migrate-up:
	@echo "Applying migrations..."
	docker-compose exec pdf-extractor alembic upgrade head

migrate-down:
	@echo "Reverting last migration..."
	docker-compose exec pdf-extractor alembic downgrade -1

db-shell:
	@echo "Opening PostgreSQL shell..."
	docker-compose exec postgres psql -U pdfuser -d pdfdb

test:
	@echo "Running tests..."
	docker-compose build
	docker-compose exec pdf-extractor poetry run pytest

test-cov:
	@echo "Running tests with coverage..."
	docker-compose exec pdf-extractor poetry run pytest --cov=app --cov-report=term --cov-report=html

# Default target
.DEFAULT_GOAL := help