.PHONY: help install run dev test clean

# Python environment settings
VENV = .venv
PYTHON = $(VENV)/bin/python
UVICORN = $(VENV)/bin/uvicorn
PYTEST = $(VENV)/bin/pytest

# Server configuration
HOST ?= 0.0.0.0
PORT ?= 8000

help: ## Show available commands
	@echo "AI Development Team Platform - Management Commands"
	@echo "----------------------------------------------------"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Setup virtual environment and install all dependencies
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run: dev ## Alias for dev

dev: ## Start the server locally with auto-reload at http://localhost:8000
	@echo "🚀 Starting AI Development Team Dashboard & Server at http://localhost:$(PORT)..."
	@PYTHONPATH=. $(PYTHON) -m uvicorn app.api.app:app --host $(HOST) --port $(PORT) --reload

test: ## Run full test suite with pytest
	PYTHONPATH=. $(PYTEST) -v

clean: ## Clean python bytecode and cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
