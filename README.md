# Control de Gastos

![CI](https://github.com/Nicokac/control_gastos/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-95%25-green)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-5.2-green)
![License](https://img.shields.io/badge/license-private-lightgrey)

> Aplicación web para el control y seguimiento de finanzas personales desarrollada con Django.

---

## 📋 Tabla de Contenidos

- [Estado del Proyecto](#estado-del-proyecto)
- [Descripción](#descripción)
- [Características Principales](#características-principales)
- [Stack Tecnológico](#stack-tecnológico)
- [Instalación](#instalación)
- [Variables de Entorno](#variables-de-entorno)
- [Testing](#testing)
- [Deploy a Producción](#deploy-a-producción)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Comandos Útiles](#comandos-útiles)
- [Pipeline de Calidad](#pipeline-de-calidad)
- [Roadmap](#roadmap)
- [Autor](#autor)

---

## Estado del Proyecto

| Métrica | Valor |
|---------|-------|
| Tests | 556 |
| Coverage | 95.29% |
| Python | 3.11+ |
| Django | 5.2 |
| Estado | 🟢 **Listo para Producción** |

---

## Descripción

**Control de Gastos** permite a los usuarios:

- Registrar gastos e ingresos con soporte multimoneda (ARS/USD)
- Conversión automática a ARS usando tipo de cambio configurable
- Categorizar transacciones con categorías predefinidas y personalizadas
- Crear metas de ahorro con seguimiento de depósitos y retiros
- Establecer presupuestos mensuales por categoría con alertas visuales
- Visualizar dashboard con resumen financiero y gráficos de distribución
- Comparar gastos e ingresos con el mes anterior

---

## Características Principales

### 💰 Gestión de Gastos e Ingresos
- Registro con fecha, descripción, monto y categoría
- Soporte multimoneda (ARS/USD) con conversión automática
- Filtros por mes, año y categoría
- Paginación en listados

### 📊 Dashboard Interactivo
- Resumen de balance mensual (ingresos vs gastos)
- Comparación porcentual con mes anterior
- Estado de presupuestos con alertas visuales
- Progreso de metas de ahorro
- Gráfico de distribución de gastos por categoría
- Últimas transacciones

### 🎯 Presupuestos
- Presupuestos mensuales por categoría de gasto
- Umbral de alerta configurable (default 80%)
- Estados: OK, Alerta, Excedido
- Función de copiar presupuestos del mes anterior

### 🐷 Metas de Ahorro
- Crear metas con objetivo y fecha límite
- Registrar depósitos y retiros
- Seguimiento de progreso porcentual
- Auto-completado cuando se alcanza el objetivo

### 🏷️ Categorías
- Categorías de sistema predefinidas
- Categorías personalizadas por usuario
- Tipos: Gasto e Ingreso
- Iconos y colores personalizables

### 🔒 Seguridad
- Rate limiting con django-axes (5 intentos, bloqueo 2 horas)
- Headers de seguridad (HSTS, CSP, X-Frame-Options)
- Logging de eventos de seguridad
- Validación obligatoria de SECRET_KEY

---

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| **Backend** | Python 3.11+ / Django 5.2 |
| **Frontend** | Django Templates + Bootstrap 5 |
| **Base de datos** | SQLite (dev) / PostgreSQL (prod) |
| **Gráficos** | Chart.js |
| **Iconos** | Bootstrap Icons |
| **CI/CD** | GitHub Actions |
| **Linting** | Ruff |
| **Testing** | pytest + pytest-cov |
| **Pre-commit** | pre-commit hooks |
| **Rate Limiting** | django-axes |

---

## Instalación

### Requisitos Previos

- Python 3.11 o superior
- pip
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/Nicokac/control_gastos.git
cd control_gastos
```

### 2. Crear y activar entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
# Desarrollo
pip install -r requirements/dev.txt

# Producción
pip install -r requirements/prod.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar ejemplo
cp .env.example .env

# Generar SECRET_KEY
python manage.py generate_secret_key

# Editar .env con tus valores
```

### 5. Aplicar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

Acceder a http://127.0.0.1:8000

---

## Variables de Entorno

### Desarrollo (`.env`)

```env
# Django
SECRET_KEY=tu-clave-secreta-de-50-caracteres-minimo
DJANGO_SETTINGS_MODULE=config.settings.dev
DEBUG=True

# Base de datos (opcional en dev, usa SQLite por defecto)
# DATABASE_URL=postgres://user:password@localhost:5432/control_gastos
```

### Producción

```env
# Django (REQUERIDO)
SECRET_KEY=clave-secreta-segura-generada-con-generate_secret_key
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=False

# Hosts permitidos (REQUERIDO)
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# Base de datos PostgreSQL (REQUERIDO)
DB_NAME=control_gastos_prod
DB_USER=postgres
DB_PASSWORD=password-seguro
DB_HOST=localhost
DB_PORT=5432

# Email (opcional, para notificaciones de errores)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
DEFAULT_FROM_EMAIL=noreply@tudominio.com

# Admins para notificaciones de errores
ADMINS=Tu Nombre:tu-email@gmail.com
```

### Referencia de Variables

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `SECRET_KEY` | ✅ Sí | - | Clave secreta Django (mín. 50 caracteres) |
| `DEBUG` | No | `False` | Modo debug |
| `ALLOWED_HOSTS` | ✅ Prod | `localhost` | Hosts permitidos |
| `DB_NAME` | ✅ Prod | `db.sqlite3` | Nombre de la base de datos |
| `DB_USER` | ✅ Prod | - | Usuario PostgreSQL |
| `DB_PASSWORD` | ✅ Prod | - | Contraseña PostgreSQL |
| `DB_HOST` | ✅ Prod | `localhost` | Host de la base de datos |
| `DB_PORT` | No | `5432` | Puerto PostgreSQL |

---

## Testing

### Ejecutar tests

```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=apps --cov-report=term-missing

# Con reporte HTML
pytest --cov=apps --cov-report=html
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac

# Tests específicos
pytest apps/expenses/
pytest apps/expenses/tests/test_views.py
pytest -k "test_create_expense"
```

### Verificar coverage mínimo (80%)

```bash
pytest --cov=apps --cov-fail-under=80
```

### Resultados actuales

```
705 passed, 2 skipped
Coverage: 95.29%
```

---

## Deploy a Producción

### Checklist Pre-Deploy

```bash
# 1. Verificar seguridad
python scripts/check_security.py

# 2. Verificar configuración de producción
python manage.py check --deploy --settings=config.settings.prod

# 3. Ejecutar tests
pytest --cov=apps --cov-fail-under=80
```

### Pasos de Deploy

```bash
# 1. Configurar variables de entorno
export SECRET_KEY='tu-clave-secreta-segura'
export DJANGO_SETTINGS_MODULE='config.settings.prod'
export ALLOWED_HOSTS='tudominio.com'
export DB_NAME='control_gastos_prod'
export DB_USER='postgres'
export DB_PASSWORD='password-seguro'

# 2. Instalar dependencias
pip install -r requirements/prod.txt

# 3. Verificar seguridad
python scripts/check_security.py

# 4. Aplicar migraciones
python manage.py migrate

# 5. Recolectar archivos estáticos
python manage.py collectstatic --noinput

# 6. Verificar configuración
python manage.py check --deploy

# 7. Iniciar servidor (ejemplo con Gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Configuración de Seguridad en Producción

El proyecto incluye las siguientes configuraciones de seguridad en `prod.py`:

| Configuración | Valor | Descripción |
|---------------|-------|-------------|
| `SECURE_HSTS_SECONDS` | 31536000 | HSTS por 1 año |
| `SECURE_SSL_REDIRECT` | True | Redirige HTTP a HTTPS |
| `SESSION_COOKIE_SECURE` | True | Cookies solo por HTTPS |
| `CSRF_COOKIE_SECURE` | True | CSRF solo por HTTPS |
| `X_FRAME_OPTIONS` | DENY | Previene clickjacking |
| `AXES_FAILURE_LIMIT` | 5 | Intentos de login |
| `AXES_COOLOFF_TIME` | 2 horas | Tiempo de bloqueo |

---

## Estructura del Proyecto

```
control_gastos/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── apps/                       # Aplicaciones Django
│   ├── budgets/               # Presupuestos mensuales
│   ├── categories/            # Gestión de categorías
│   ├── core/                  # Mixins, constantes, utilidades
│   │   ├── management/commands/
│   │   │   ├── generate_secret_key.py
│   │   │   ├── axes_status.py
│   │   │   └── view_logs.py
│   │   └── logging.py         # Utilidades de logging
│   ├── expenses/              # Registro de gastos
│   ├── income/                # Registro de ingresos
│   ├── reports/               # Dashboard y reportes
│   ├── savings/               # Metas de ahorro
│   └── users/                 # Autenticación y perfiles
├── config/                    # Configuración del proyecto
│   └── settings/
│       ├── base.py            # Configuración común
│       ├── dev.py             # Desarrollo
│       └── prod.py            # Producción
├── logs/                      # Archivos de log
├── scripts/
│   └── check_security.py      # Verificación de seguridad
├── static/                    # Archivos estáticos
├── templates/                 # Templates HTML
├── requirements/
│   ├── base.txt              # Dependencias comunes
│   ├── dev.txt               # Desarrollo
│   └── prod.txt              # Producción
├── .env.example              # Ejemplo de variables de entorno
├── .pre-commit-config.yaml   # Configuración pre-commit
├── pyproject.toml            # Configuración de herramientas
└── manage.py
```

---

## Comandos Útiles

### Django

```bash
# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Superusuario
python manage.py createsuperuser

# Shell
python manage.py shell

# Verificar proyecto
python manage.py check
python manage.py check --deploy --settings=config.settings.prod
```

### Seguridad

```bash
# Generar SECRET_KEY
python manage.py generate_secret_key
python manage.py generate_secret_key --env-format

# Ver estado de rate limiting
python manage.py axes_status
python manage.py axes_status --clear

# Ver logs de seguridad
python manage.py view_logs --type security
python manage.py view_logs --type error --lines 50

# Verificar configuración de seguridad
python scripts/check_security.py
```

### Testing y Calidad

```bash
# Tests
pytest
pytest --cov=apps --cov-report=html

# Linting
ruff check apps/
ruff check apps/ --fix

# Formateo
ruff format apps/

# Pre-commit
pre-commit run --all-files
```

---

## Pipeline de Calidad

### Pre-commit Hooks (Local)

Antes de cada commit se ejecutan automáticamente:

- ✅ Ruff (lint + autofix)
- ✅ Ruff-format
- ✅ detect-secrets
- ✅ Validaciones de whitespace, conflictos, tamaños

### GitHub Actions (CI)

En cada push/PR se ejecutan:

| Job | Descripción | Duración |
|-----|-------------|----------|
| `lint` | Ruff check + format | ~30s |
| `test` | pytest + coverage ≥80% | ~4min |
| `security` | pip-audit + safety | ~1min |
| `django-checks` | System checks + migrations | ~1min |
| `build` | Collectstatic + verify | ~1min |

---

## Flujo de Git

| Rama | Propósito |
|------|-----------|
| `main` | Código estable, listo para producción |
| `develop` | Integración de features |
| `feature/*` | Desarrollo de nuevas funcionalidades |
| `fix/*` | Corrección de bugs |

### Formato de Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(expenses): add expense creation form
fix(budgets): correct alert threshold calculation
perf(reports): optimize dashboard queries
docs(readme): update installation instructions
test(savings): add movement validation tests
ci: add GitHub Actions pipeline
```

---

## Roadmap

### MVP ✅ Completado

- [x] Sistema de autenticación
- [x] CRUD de categorías
- [x] CRUD de gastos (multimoneda)
- [x] CRUD de ingresos (multimoneda)
- [x] Metas de ahorro con movimientos
- [x] Presupuestos mensuales con alertas
- [x] Dashboard con gráficos
- [x] Rate limiting y seguridad
- [x] CI/CD con GitHub Actions
- [x] Coverage ≥80%

### Próximas Features

- [ ] Exportación a Excel/PDF
- [ ] Filtros avanzados por rango de fechas
- [ ] Gráficos de evolución mensual
- [ ] Transacciones recurrentes
- [ ] PWA (Progressive Web App)
- [ ] Notificaciones por email
- [ ] Caching con Redis
- [ ] 2FA (Autenticación de dos factores)

---

## Apps y Modelos

### Apps

| App | Descripción | Estado |
|-----|-------------|--------|
| `core` | Mixins, constantes, utilidades, logging | ✅ |
| `users` | Registro, login, logout, perfil | ✅ |
| `categories` | CRUD categorías (sistema + custom) | ✅ |
| `expenses` | CRUD gastos, multimoneda | ✅ |
| `income` | CRUD ingresos, multimoneda | ✅ |
| `savings` | Metas de ahorro, movimientos | ✅ |
| `budgets` | Presupuestos mensuales, alertas | ✅ |
| `reports` | Dashboard, gráficos | ✅ |

### Modelos Principales

- **Expense/Income**: Transacciones con soporte multimoneda
- **Budget**: Presupuestos mensuales por categoría
- **Saving**: Metas de ahorro con progreso
- **SavingMovement**: Depósitos y retiros
- **Category**: Categorías de sistema y personalizadas

---

## Licencia

Este proyecto es de uso privado.

---

## Autor

**Nicolás Kachuk**

[![GitHub](https://img.shields.io/badge/GitHub-Nicokac-blue?logo=github)](https://github.com/Nicokac)
