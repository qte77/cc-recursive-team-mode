.SILENT:
.ONESHELL:
.PHONY: setup_dev lint type_check test test_coverage test_integration validate quick_validate help
.DEFAULT_GOAL := help

setup_dev:  ## Install all dev dependencies
	pip install uv -q
	uv sync --all-groups

lint:  ## Format and lint with ruff
	uv run ruff format src tests
	uv run ruff check --fix src tests

type_check:  ## Static type checking with pyright
	uv run pyright

test:  ## Run all tests
	uv run pytest

test_coverage:  ## Run tests with coverage report
	uv run pytest --cov

test_integration:  ## Run integration tests (real claude -p, costs money)
	uv run pytest -m integration -v

validate:  ## Complete pre-commit validation: lint + type_check + test_coverage
	set -e
	$(MAKE) -s lint
	$(MAKE) -s type_check
	$(MAKE) -s test_coverage
	@echo "Validation passed"

quick_validate:  ## Fast check: lint + type_check only
	set -e
	$(MAKE) -s lint
	-$(MAKE) -s type_check

help:  ## Show available recipes
	@awk '/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, substr($$0, index($$0,"##")+3) }' $(MAKEFILE_LIST)
