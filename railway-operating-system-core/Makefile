# =========================================================
# Makefile for Railway Operating System
# Docker container management and operations
# =========================================================

.PHONY: help build up down restart logs clean test dev prod migrate

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)Railway Operating System - Docker Management$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "$(GREEN)Usage:$(NC)\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

dev: ## Start development environment with hot-reload
	@echo "$(GREEN)Starting development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml up --build

dev-detached: ## Start development environment in background
	@echo "$(GREEN)Starting development environment (detached)...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d --build

dev-down: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Show development logs
	docker-compose -f docker-compose.dev.yml logs -f

##@ Production

prod: ## Start production environment
	@echo "$(GREEN)Starting production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml.new up --build -d

prod-down: ## Stop production environment
	@echo "$(YELLOW)Stopping production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml.new down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml.new logs -f

##@ Build

build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build

build-backend: ## Build backend image only
	@echo "$(GREEN)Building backend image...$(NC)"
	docker-compose build backend

build-frontend: ## Build frontend image only
	@echo "$(GREEN)Building frontend image...$(NC)"
	docker-compose build frontend

build-no-cache: ## Build all images without cache
	@echo "$(GREEN)Building Docker images (no cache)...$(NC)"
	docker-compose build --no-cache

##@ Container Management

up: ## Start all services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker-compose restart

stop: ## Stop all services without removing
	@echo "$(YELLOW)Stopping services...$(NC)"
	docker-compose stop

ps: ## List running containers
	docker-compose ps

##@ Logs

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-postgres: ## Show PostgreSQL logs
	docker-compose logs -f postgres

logs-redis: ## Show Redis logs
	docker-compose logs -f redis

##@ Database

migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	docker-compose run --rm migrate

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U railway_user -d railway_db

db-backup: ## Backup database
	@echo "$(GREEN)Creating database backup...$(NC)"
	docker-compose exec postgres pg_dump -U railway_user railway_db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from backup (specify FILE=backup.sql)
	@echo "$(GREEN)Restoring database from $(FILE)...$(NC)"
	docker-compose exec -T postgres psql -U railway_user -d railway_db < $(FILE)

##@ CLI

cli: ## Run interactive CLI application
	@echo "$(GREEN)Starting CLI application...$(NC)"
	docker-compose run --rm cli

cli-shell: ## Open shell in CLI container
	docker-compose run --rm cli /bin/bash

##@ Testing

test: ## Run all tests
	@echo "$(GREEN)Running tests...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm backend pytest

test-backend: ## Run backend tests
	@echo "$(GREEN)Running backend tests...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm backend pytest tests/

test-coverage: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	docker-compose -f docker-compose.dev.yml run --rm backend pytest --cov=. --cov-report=html

##@ Health & Monitoring

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@docker-compose ps | grep -E "(healthy|Up)"

status: ## Show detailed status
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

stats: ## Show resource usage statistics
	docker stats $$(docker-compose ps -q)

##@ Cleanup

clean: ## Remove all containers, volumes, and networks
	@echo "$(RED)Cleaning up all containers, volumes, and networks...$(NC)"
	docker-compose down -v --remove-orphans

clean-images: ## Remove all project images
	@echo "$(RED)Removing all project Docker images...$(NC)"
	docker-compose down --rmi all

clean-all: ## Complete cleanup including volumes
	@echo "$(RED)Complete cleanup (containers, images, volumes)...$(NC)"
	docker-compose down -v --rmi all --remove-orphans

prune: ## Prune unused Docker resources
	@echo "$(YELLOW)Pruning unused Docker resources...$(NC)"
	docker system prune -f

prune-all: ## Prune all unused Docker resources including volumes
	@echo "$(RED)Pruning all unused Docker resources...$(NC)"
	docker system prune -a --volumes -f

##@ Development Tools

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

shell-postgres: ## Open shell in postgres container
	docker-compose exec postgres /bin/bash

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

##@ Security

scan: ## Scan images for vulnerabilities (requires Docker Scout or Trivy)
	@echo "$(BLUE)Scanning images for vulnerabilities...$(NC)"
	@if command -v trivy > /dev/null; then \
		trivy image railway-backend:latest; \
		trivy image railway-frontend:latest; \
	else \
		echo "$(YELLOW)Trivy not installed. Install with: brew install trivy$(NC)"; \
	fi

##@ Quick Commands

quick-start: build up migrate ## Quick start: build, start, and migrate
	@echo "$(GREEN)Railway OS is running!$(NC)"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"

quick-stop: down ## Quick stop all services

fresh-start: clean build up migrate ## Fresh start: clean, build, start, migrate
	@echo "$(GREEN)Fresh Railway OS environment ready!$(NC)"
