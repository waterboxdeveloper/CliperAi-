.PHONY: help install-make build dev prod start stop down restart logs shell clean ps test format lint

# Default target - show help
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║              CLIPER - Makefile Commands                        ║"
	@echo "║          Video Processing CLI Tool by opino.tech               ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "🔧 Setup Commands:"
	@echo "  make install-make    Install make on macOS (if not installed)"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make build          Build Docker images"
	@echo "  make dev            Start in development mode (interactive)"
	@echo "  make prod           Start in production/detached mode"
	@echo "  make start          Alias for 'make dev'"
	@echo "  make stop           Stop running containers"
	@echo "  make down           Stop and remove containers"
	@echo "  make restart        Restart all services"
	@echo "  make logs           View container logs (follow mode)"
	@echo "  make shell          Open shell inside container"
	@echo "  make ps             Show running containers"
	@echo ""
	@echo "🧹 Cleanup Commands:"
	@echo "  make clean          Remove containers, volumes, and images"
	@echo "  make clean-cache    Clean Python cache and WhisperX models"
	@echo ""
	@echo "💻 Development Commands:"
	@echo "  make test           Run tests inside container"
	@echo "  make format         Format code with black and isort"
	@echo "  make lint           Run code linting"
	@echo ""
	@echo "📝 Usage Examples:"
	@echo "  make build && make dev    # Build and start development"
	@echo "  make logs                 # View logs in real-time"
	@echo "  make shell                # Debug inside container"

# Install make on macOS using Homebrew
install-make:
	@if command -v make >/dev/null 2>&1; then \
		echo "✅ make is already installed (version: $$(make --version | head -n1))"; \
	else \
		echo "📦 Installing make via Homebrew..."; \
		if ! command -v brew >/dev/null 2>&1; then \
			echo "❌ Homebrew not found. Installing Homebrew first..."; \
			/bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; \
		fi; \
		brew install make; \
		echo "✅ make installed successfully!"; \
	fi

# Build Docker images
build:
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ Build complete!"

# Start in development mode (interactive, attached)
dev:
	@echo "🚀 Starting CLIPER in development mode..."
	@echo "💡 Tip: Use Ctrl+C to stop"
	docker-compose up

# Start in production mode (detached)
prod:
	@echo "🚀 Starting CLIPER in production mode (detached)..."
	docker-compose up -d
	@echo "✅ CLIPER is running in the background"
	@echo "📋 View logs: make logs"
	@echo "🛑 Stop: make stop"

# Alias for dev
start: dev

# Stop containers without removing them
stop:
	@echo "⏸️  Stopping containers..."
	docker-compose stop
	@echo "✅ Containers stopped"

# Stop and remove containers
down:
	@echo "🛑 Stopping and removing containers..."
	docker-compose down
	@echo "✅ Containers removed"

# Restart all services
restart:
	@echo "🔄 Restarting services..."
	docker-compose restart
	@echo "✅ Services restarted"

# View logs (follow mode)
logs:
	@echo "📋 Viewing logs (Ctrl+C to exit)..."
	docker-compose logs -f

# Open shell inside the container
shell:
	@echo "💻 Opening shell in cliper container..."
	docker-compose exec cliper /bin/bash

# Show running containers
ps:
	@echo "🐳 Running containers:"
	docker-compose ps

# Clean everything (containers, volumes, images)
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v
	@if [ "$$(docker images -q cliper-cliper 2> /dev/null)" != "" ]; then \
		docker rmi cliper-cliper; \
		echo "✅ Removed Docker image"; \
	fi
	@echo "✅ Cleanup complete!"

# Clean Python cache and model cache
clean-cache:
	@echo "🧹 Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache cleaned!"

# Run tests inside container
test:
	@echo "🧪 Running tests..."
	docker-compose exec cliper uv run pytest -v
	@echo "✅ Tests complete!"

# Format code with black and isort
format:
	@echo "🎨 Formatting code..."
	docker-compose exec cliper uv run black .
	docker-compose exec cliper uv run isort .
	@echo "✅ Code formatted!"

# Run linting
lint:
	@echo "🔍 Running linters..."
	docker-compose exec cliper uv run black --check .
	docker-compose exec cliper uv run isort --check .
	docker-compose exec cliper uv run mypy src/
	@echo "✅ Linting complete!"

# Quick rebuild (clean + build + dev)
rebuild: clean build dev

# Production deployment helper
deploy: build prod
	@echo "🚀 Production deployment complete!"
	@make ps
