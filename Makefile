.PHONY: help test coverage coverage-html lint lint-fix format format-check check clean pre-commit

# Variables
PYTHON = python
PYTEST = pytest
COVERAGE_MIN = 80

help:
	@echo "Comandos disponibles:"
	@echo "  make test          - Ejecutar tests"
	@echo "  make coverage      - Ejecutar tests con coverage (terminal)"
	@echo "  make coverage-html - Ejecutar tests con coverage (HTML)"
	@echo "  make lint          - Ejecutar linter (ruff check)"
	@echo "  make lint-fix      - Ejecutar linter con autofix (ruff --fix)"
	@echo "  make format        - Formatear código (ruff format)"
	@echo "  make format-check  - Verificar formato sin modificar archivos"
	@echo "  make check         - Lint + format + pre-commit"
	@echo "  make clean         - Limpiar archivos generados"

test:
	$(PYTEST) -v

coverage:
	$(PYTEST) --cov=apps --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)

coverage-html:
	$(PYTEST) --cov=apps --cov-report=html --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)
	@echo "Reporte HTML generado en htmlcov/index.html"

# Ejecutar linter (solo check)
lint:
	ruff check apps/

# Corregir errores de linting
lint-fix:
	ruff check apps/ --fix

# Formatear código
format:
	ruff format apps/

# Verificar formato sin cambiar archivos
format-check:
	ruff format apps/ --check

# Ejecutar todos los checks (lint-fix + format + pre-commit)
check: lint-fix format
	pre-commit run --all-files

# Ejecutar pre-commit en todos los archivos
pre-commit:
	pre-commit run --all-files

clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
