# Guía de Testing

## Comandos básicos

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con verbose
pytest -v

# Ejecutar tests de una app
pytest apps/expenses/tests/

# Ejecutar un archivo específico
pytest apps/expenses/tests/test_models.py

# Ejecutar un test específico
pytest apps/expenses/tests/test_models.py::TestExpenseModel::test_create_expense_ars
```

## Coverage

```bash
# Coverage con reporte en terminal
pytest --cov=apps

# Coverage con líneas faltantes
pytest --cov=apps --cov-report=term-missing

# Coverage con reporte HTML
pytest --cov=apps --cov-report=html

# Coverage de una app específica
pytest --cov=apps.expenses --cov-report=term-missing apps/expenses/tests/

# Abrir reporte HTML (Windows)
start htmlcov/index.html

# Abrir reporte HTML (Linux/Mac)
open htmlcov/index.html
```

## Limpieza de cache

### Windows (PowerShell)

```powershell
# Limpiar __pycache__
Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory -Force | Remove-Item -Recurse -Force

# Limpiar .pytest_cache
Get-ChildItem -Path . -Filter .pytest_cache -Recurse -Directory -Force | Remove-Item -Recurse -Force

# Limpiar archivos .pyc
Get-ChildItem -Path . -Filter *.pyc -Recurse -Force | Remove-Item -Force
```

### Linux/Mac (bash)

```bash
# Limpiar __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Limpiar .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# Limpiar archivos .pyc
find . -type f -name "*.pyc" -delete

# O usar pytest directamente
pytest --cache-clear
```

## Markers

```bash
# Excluir tests lentos
pytest -m "not slow"

# Solo tests unitarios
pytest -m "unit"

# Solo tests de integración
pytest -m "integration"
```

## Opciones útiles

```bash
# Parar en el primer fallo
pytest -x

# Solo tests que fallaron antes
pytest --lf

# Tests que contengan "nombre"
pytest -k "nombre"

# Mostrar prints en tests
pytest -s

# Paralelizar tests (requiere pytest-xdist)
pytest -n auto
```
```

### 7.2 Commit

```bash
git add docs/testing.md
git commit -m "docs: add testing guide with commands"
```