# AgeingAnalysis Development Makefile

.PHONY: help install install-dev test test-unit test-integration test-gui lint format security clean build docs docs-serve release

# Default target
help:
	@echo "AgeingAnalysis Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup:"
	@echo "  install        Install the package"
	@echo "  install-dev    Install package with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-gui       Run GUI tests only (requires display)"
	@echo "  coverage       Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run all linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  security       Run security checks"
	@echo "  pre-commit     Run all pre-commit hooks"
	@echo ""
	@echo "Documentation:"
	@echo "  docs           Build documentation"
	@echo "  docs-serve     Build and serve documentation locally"
	@echo ""
	@echo "Release:"
	@echo "  build          Build distribution packages"
	@echo "  release        Create a new release (bump version and tag)"
	@echo "  clean          Clean build artifacts"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e .[dev,test,docs]
	pre-commit install
	pre-commit install --hook-type commit-msg

# Testing
test:
	pytest -v

test-unit:
	pytest -v -m "unit"

test-integration:
	pytest -v -m "integration"

test-gui:
	pytest -v -m "gui"

coverage:
	pytest --cov=ageing_analysis --cov-report=html --cov-report=term-missing

# Code Quality
lint:
	@echo "Running flake8..."
	flake8 ageing_analysis tests
	@echo "Running mypy..."
	mypy ageing_analysis
	@echo "Running bandit..."
	bandit -r ageing_analysis

format:
	@echo "Running autoflake..."
	autoflake --in-place --remove-all-unused-imports --recursive ageing_analysis tests
	@echo "Running isort..."
	isort ageing_analysis tests
	@echo "Running black..."
	black ageing_analysis tests

security:
	bandit -r ageing_analysis
	safety check

pre-commit:
	pre-commit run --all-files

# Documentation
docs:
	cd docs && make html

docs-serve: docs
	cd docs/_build/html && python -m http.server 8000

# Release
build: clean
	python -m build

release:
	cz bump --yes
	git push origin main --tags

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 