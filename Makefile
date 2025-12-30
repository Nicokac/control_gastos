.PHONY: test coverage coverage-html lint clean help

# Variables
PYTHON = python
PYTEST = pytest
COVERAGE_MIN = 80

help:
	@echo "Comandos disponibles:"
	@echo "  make test          - Ejecutar tests"
	@echo "  make coverage      - Ejecutar tests con coverage (terminal)"
	@echo "  make coverage-html - Ejecutar tests con coverage (HTML)"
	@echo "  make lint          - Ejecutar linter"
	@echo "  make clean         - Limpiar archivos generados"

test:
	$(PYTEST) -v

coverage:
	$(PYTEST) --cov=apps --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)

coverage-html:
	$(PYTEST) --cov=apps --cov-report=html --cov-report=term-missing --cov-fail-under=$(COVERAGE_MIN)
	@echo "Reporte HTML generado en htmlcov/index.html"

lint:
	ruff check apps/
	ruff format --check apps/

clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete