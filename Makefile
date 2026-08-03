.PHONY: help build up down logs shell test clean

help:
	@echo "Available commands:"
	@echo "  build      Build Docker images"
	@echo "  up         Start services"
	@echo "  down       Stop services"
	@echo "  logs       View logs"
	@echo "  shell      Open shell in backend container"
	@echo "  test       Run tests"
	@echo "  clean      Clean up containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✅ Services started:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Docs: http://localhost:8000/docs"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - Redis: localhost:6379"

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec backend bash

test:
	docker-compose exec backend pytest -v

clean:
	docker-compose down -v
	docker-compose rm -f

dev-build:
	docker-compose -f docker-compose.dev.yml build

dev-up:
	docker-compose -f docker-compose.dev.yml up -d

dev-down:
	docker-compose -f docker-compose.dev.yml down

dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

migrate:
	docker-compose exec backend alembic upgrade head

seed:
	docker-compose exec backend python seed.py