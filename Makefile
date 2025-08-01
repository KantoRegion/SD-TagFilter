.DEFAULT_GOAL := all

.PHONY: .uv
.uv: ## Check that uv is installed
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: sync
sync: .uv ## Update local packages and uv.lock
	uv sync --all-extras --all-packages --group lint --group dev

.PHONY: format
format: ## Format the code
	uv run ruff format
	uv run ruff check --fix --fix-only

.PHONY: lint
lint: ## Lint the code
	uv run ruff format --check
	uv run ruff check

.PHONY: typecheck-pyright
typecheck-pyright:
	@# PYRIGHT_PYTHON_IGNORE_WARNINGS avoids the overhead of making a request to github on every invocation
	PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright

.PHONY: typecheck
typecheck: typecheck-pyright ## Run static type checking

.PHONY: test
test: ## Run tests and collect coverage data
	uv run coverage run -m pytest
	@uv run coverage report

.PHONY: test-fast
test-fast: ## Same as test except no coverage and 4x faster depending on hardware
	uv run pytest -n auto --dist=loadgroup

.PHONY: testcov
testcov: test ## Run tests and generate an HTML coverage report
	@echo "building coverage html"
	@uv run coverage html

.PHONY: all
all: format lint typecheck testcov ## Run code formatting, linting, static type checks, and tests with coverage report generation