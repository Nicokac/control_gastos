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
- [Estado de Calidad y Métricas Verificadas](#-estado-de-calidad-y-métricas-verificadas)
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
| Tests | 700+ |
| Coverage | ≥80% (enforced) |
| Python | 3.11+ |
| Django | 5.2 |
| CI Jobs | 5 |
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

# Admin para notificaciones
ADMIN_EMAIL=admin@tudominio.com
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

## 📊 Estado de Calidad y Métricas Verificadas

> Esta sección documenta **métricas reales de calidad**, ejecutadas manualmente o por CI,  
> y sirve como **fuente de verdad** para revisiones humanas y agentes de IA.

### 🔍 Última Ejecución Verificada

| Ítem | Valor |
|-----|------|
| Fecha | **2026-02-10** |
| Entorno | Local (Windows) |
| Python | 3.12.0 |
| Django | 5.2.9 |
| Settings | `config.settings.dev` |
| Commit | *no fijado (ejecución local)* |

Resultado:

| Ítem | Valor |
|-----|------|
| ✅ |  713 tests pasados |
| ⏭️ |  2 skipped |
| ❌ |  0 fallos |
| ⏱️ |  Duración total: 4m 49s |


📈 Coverage
```bash
pytest --cov=apps --cov-report=term-missing
```

Resultado verificado:

| Métrica | Valor |
|-----|------|
| Coverage total|	95.20%|
|Coverage mínimo requerido|	80%|
|Estado|	✅ Cumple|

```bash
python manage.py check --deploy --settings=config.settings.prod
System check identified no issues (0 silenced).
```

---

## Deploy a Producción

### Plataforma Actual

| Item | Valor |
|------|-------|
| **Hosting** | Render (Free tier) |
| **URL** | `https://control-gastos-XXXX.onrender.com` |
| **Base de datos** | PostgreSQL (Render) |
| **CI/CD** | GitHub Actions → Render Deploy Hook |

---

### Variables de Entorno (Render)

Configurar en **Render Dashboard → Environment**:

| Variable | Requerida | Ejemplo | Notas |
|----------|-----------|---------|-------|
| `SECRET_KEY` | ✅ | `django-insecure-...` (50+ chars) | Generar con `python manage.py generate_secret_key` |
| `DJANGO_SETTINGS_MODULE` | ✅ | `config.settings.prod` | |
| `ALLOWED_HOSTS` | ✅ | `control-gastos-XXXX.onrender.com` | Sin `https://` |
| `DB_NAME` | ✅ | `control_gastos_db` | Desde Render PostgreSQL |
| `DB_USER` | ✅ | `control_gastos_user` | Desde Render PostgreSQL |
| `DB_PASSWORD` | ✅ | `***` | Desde Render PostgreSQL |
| `DB_HOST` | ✅ | `dpg-XXXX.render.com` | Desde Render PostgreSQL |
| `DB_PORT` | No | `5432` | Default |
| `ADMIN_EMAIL` | No | `admin@example.com` | Para alertas de errores |

---

### Checklist Pre-Deploy
```bash
# 1. Tests pasan
pytest --cov=apps --cov-fail-under=80

# 2. Lint limpio
ruff check apps/

# 3. Security checks
python manage.py check --deploy --settings=config.settings.prod

# 4. Migraciones al día
python manage.py makemigrations --check --dry-run
```

---

### Proceso de Deploy

#### Deploy Automático (Recomendado)

1. Push a `main` triggerea deploy automático via GitHub Actions
2. El workflow ejecuta tests → si pasan → deploy hook a Render
```bash
git checkout main
git merge develop
git push origin main
# Deploy automático en ~5 minutos
```

#### Deploy Manual (Emergencia)

1. Ir a **Render Dashboard → Manual Deploy**
2. Seleccionar commit
3. Click "Deploy"

---

### Verificación Post-Deploy
```bash
# 1. Healthcheck
curl https://control-gastos-XXXX.onrender.com/healthz/
# Respuesta esperada: "ok"

# 2. Verificar app carga
curl -I https://control-gastos-XXXX.onrender.com/
# Respuesta esperada: HTTP 200 o 302 (redirect a login)

# 3. Revisar logs en Render Dashboard
# Render → Service → Logs
```

---

### Rollback

#### Opción 1: Render Dashboard (Más rápido)

1. Ir a **Render → Service → Events**
2. Encontrar deploy anterior exitoso
3. Click "Rollback to this deploy"

#### Opción 2: Git Revert
```bash
# Identificar commit problemático
git log --oneline -5

# Revertir
git revert
git push origin main
# Deploy automático del revert
```

#### Opción 3: Redeploy commit específico

1. Render Dashboard → Manual Deploy
2. Seleccionar commit anterior estable
3. Deploy

---

### Troubleshooting

#### ❌ Error: "Application failed to respond"

**Causa probable:** Cold start de Render Free tier (spin down después de 15 min inactividad)

**Solución:**
- Esperar 30-60 segundos y reintentar
- Configurar UptimeRobot para ping cada 5 min a `/healthz/`

---

#### ❌ Error: "DisallowedHost"

**Causa:** `ALLOWED_HOSTS` no incluye el dominio

**Solución:**
```bash
# En Render Environment, verificar:
ALLOWED_HOSTS=control-gastos-XXXX.onrender.com
# Sin https://, sin trailing slash
```

---

#### ❌ Error: "OperationalError: could not connect to server"

**Causa:** Credenciales de DB incorrectas o DB no accesible

**Solución:**
1. Verificar variables `DB_*` en Render
2. Verificar que PostgreSQL esté running en Render
3. Verificar que el host sea el **Internal Database URL** (no external)

---

#### ❌ Error: "Invalid HTTP_HOST header"

**Causa:** Request desde dominio no permitido

**Solución:**
```bash
# Agregar dominio a ALLOWED_HOSTS (separado por coma)
ALLOWED_HOSTS=control-gastos-XXXX.onrender.com,www.tudominio.com
```

---

#### ❌ Error: "CSRF verification failed"

**Causa:** `CSRF_TRUSTED_ORIGINS` no configurado

**Solución:**
- Verificar que `ALLOWED_HOSTS` esté correcto
- El código auto-genera `CSRF_TRUSTED_ORIGINS` desde `ALLOWED_HOSTS`

---

#### ❌ Migraciones pendientes

**Síntoma:** Errores de tabla/columna no existe

**Solución:**
```bash
# En Render Shell (o local con DB de prod)
python manage.py migrate
```

---

### Monitoreo

| Servicio | URL | Propósito |
|----------|-----|-----------|
| **Healthcheck** | `/healthz/` | Verificar app running |
| **UptimeRobot** | uptimerobot.com | Evitar cold starts |
| **Render Logs** | Dashboard → Logs | Ver errores en tiempo real |
| **GitHub Actions** | Actions tab | Estado de CI/CD |

---

### Backups

#### PostgreSQL (Render)

Render Free tier **no incluye backups automáticos**.

**Backup manual:**
```bash
# Desde máquina local con acceso a DB externa
pg_dump -h  -U  -d  -F c -f backup_$(date +%Y%m%d).dump
```

**Restaurar:**
```bash
pg_restore -h  -U  -d  -c backup_YYYYMMDD.dump
```

---

### Comandos Útiles en Producción
```bash
# Render Shell (desde Dashboard → Shell)

# Ver estado de migraciones
python manage.py showmigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ver estado de rate limiting
python manage.py axes_status

# Limpiar intentos de login fallidos
python manage.py axes_reset
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

### Índices de Base de Datos

El proyecto incluye índices compuestos optimizados para queries frecuentes:

| Modelo | Índices |
|--------|---------|
| `Expense` | `(user, date)`, `(user, category)`, `(user, is_active, date)` |
| `Income` | `(user, date)`, `(user, category)`, `(user, is_active, date)` |
| `Saving` | `(user, status, is_active)` |
| `SavingMovement` | `(saving, -date, -created_at)` |
| `Category` | `(user, type)` |
| `Budget` | `(user, month, year)` |


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
│       └── email_backend.py   # Configuración de email centralizada

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
| `deploy` | Deploy a producción (placeholder) | ~30s |


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
