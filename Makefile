.PHONY: help build up down restart logs shell clean test

help:
	@echo "Available commands:"
	@echo "  make build     - Build Docker image"
	@echo "  make up        - Start containers in detached mode"
	@echo "  make down      - Stop and remove containers"
	@echo "  make restart   - Restart containers"
	@echo "  make logs      - View container logs"
	@echo "  make shell     - Open shell in running container"
	@echo "  make clean     - Remove containers, images, and volumes"
	@echo "  make test      - Run tests in container"
	@echo "  make dev       - Start development mode with hot reload"


build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Dashboard available at http://localhost:8501"

# Start in foreground (see logs)
dev:
	docker-compose up

down:
	docker-compose down

restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f streamlit

# Open shell in container
shell:
	docker-compose exec streamlit /bin/bash

# Clean up everything
clean:
	docker-compose down -v --rmi all
	@echo "Cleaned up containers, volumes, and images"

test:
	docker-compose exec streamlit pytest

# Pull latest changes and rebuild
update:
	git pull
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "Updated and restarted containers"
