# LogRAG Development Commands

.PHONY: install dev-install test lint format run-server demo clean help

# Installation
install:
	uv sync

dev-install:
	uv sync --dev

# Development
test:
	uv run pytest tests/ -v

test-coverage:
	uv run pytest tests/ --cov=src/lograg --cov-report=html

lint:
	uv run ruff check src/ tests/
	uv run mypy src/

format:
	uv run black src/ tests/ scripts/
	uv run ruff check --fix src/ tests/

# Running
run-server:
	uv run lograg-server

run-server-dev:
	uv run python -m lograg.server --dev

# Demo and utilities
demo:
	uv run python scripts/generate_sample_data.py --all

populate-data:
	uv run python scripts/generate_sample_data.py --populate 200

search-demo:
	uv run python scripts/generate_sample_data.py --demo

# Cleanup
clean:
	rm -rf vector_db/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf src/lograg.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker (optional)
docker-build:
	docker build -t lograg:latest .

docker-run:
	docker run -p 8000:8000 -v $(PWD)/vector_db:/app/vector_db lograg:latest

# Help
help:
	@echo "LogRAG Development Commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install        Install production dependencies"
	@echo "  dev-install    Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  test           Run tests"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code"
	@echo ""
	@echo "Running:"
	@echo "  run-server     Start MCP server"
	@echo "  run-server-dev Start MCP server in development mode"
	@echo ""
	@echo "Demo:"
	@echo "  demo           Generate sample data and run search demo"
	@echo "  populate-data  Generate sample log data"
	@echo "  search-demo    Run search demonstration"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean          Remove generated files and caches"
