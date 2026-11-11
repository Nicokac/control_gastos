# Control de Gastos

![CI](https://github.com/Nicokac/control_gastos/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-86%25-green)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.2-green)
![Flutter](https://img.shields.io/badge/flutter-3.44-blue)
![License](https://img.shields.io/badge/license-private-lightgrey)

> Finanzas personales para Argentina: gastos e ingresos en pesos y dólares, gastos fijos y cuotas, metas de ahorro y avisos. Web en Django y app Android en Flutter, sobre la misma API.

**Web:** [controldegastos.ar](https://controldegastos.ar) · **Android:** Google Play (`app.controlgastos`)

---

## Documentación

| Documento | Qué tiene |
|---|---|
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Componentes, diagramas, flujos (login, push, email) y modelo de datos |
| [`docs/database.dbml`](docs/database.dbml) | Esquema de la base para [dbdiagram.io](https://dbdiagram.io/d) |
| [`docs/OPERACION.md`](docs/OPERACION.md) | Deploy, rollback, variables de entorno, backups y problemas comunes |
| [`mobile/README.md`](mobile/README.md) | Correr, testear y publicar la app Android |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Decisiones de diseño (`D-XXX`) y deuda técnica (`DT-XXX`) con su porqué |
| [`docs/FLUTTER_ROADMAP.md`](docs/FLUTTER_ROADMAP.md) | Estado y registro de avance de la app mobile |
| [`docs/testing.md`](docs/testing.md) | Comandos de pytest |
| [`docs/AUDITORIA_SEGURIDAD.md`](docs/AUDITORIA_SEGURIDAD.md) | Auditoría de seguridad |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de versiones web y mobile |
| `/api/v1/docs/` | Documentación interactiva de la API (Swagger), generada del código |

---

## Funcionalidades

- **Gastos e ingresos** en ARS o USD, con la cotización oficial del día (dolarapi.com) y conversión a pesos.
- **Categorías** de sistema y propias, agrupadas en grupo → subcategoría, con límite mensual opcional por subcategoría.
- **Gastos fijos** con día de vencimiento, cuotas y débito automático; **ingresos fijos** con día esperado.
- **Metas de ahorro** con depósitos y retiros, gastos vinculados a una meta y sugerencia de pasar el sobrante del mes.
- **Gastos compartidos** del hogar, con miembros que no necesitan cuenta.
- **Dashboard** con balance, proyección al cierre, distribución por categoría y evolución mensual. El mes financiero puede empezar el día que elija el usuario.
- **Importación de resúmenes de tarjeta** (beta, Banco Macro).
- **Avisos push** en la app: gastos fijos por vencer o vencidos y alertas por umbral de gasto.
- **Cuenta:** registro con verificación de email, login con email o usuario, recuperación de contraseña.

---

## Stack

| | Tecnología |
|---|---|
| Backend | Python 3.12, Django 5.2, Django REST Framework, SimpleJWT |
| Web | Templates de Django, Bootstrap 5.3, Bootstrap Icons, Chart.js, flatpickr |
| Mobile | Flutter 3.44, Riverpod, Dio, GoRouter, Firebase Cloud Messaging |
| Base de datos | PostgreSQL (producción), SQLite (desarrollo y tests) |
| Infraestructura | Render, Cloudflare (DNS y R2), Brevo (email), Sentry |
| Calidad | pytest, Ruff, pre-commit, GitHub Actions |

---

## Puesta en marcha (backend y web)

Requisitos: Python 3.12 y Git. En Windows, los comandos son para PowerShell.

```powershell
git clone https://github.com/Nicokac/control_gastos.git
cd control_gastos

python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Linux/Mac: source .venv/bin/activate
pip install -r requirements/dev.txt

cp .env.example .env
python manage.py generate_secret_key  # pegar el valor en SECRET_KEY del .env

python manage.py migrate              # crea las tablas y las categorías de sistema
python manage.py createsuperuser
python manage.py runserver
```

Abrir <http://127.0.0.1:8000>. Sin más configuración se usa SQLite, los emails se imprimen en la consola y los push no se envían. Las variables opcionales (Brevo, Firebase, cron) están explicadas en [`.env.example`](.env.example); las de producción, en [`docs/OPERACION.md`](docs/OPERACION.md#variables-de-entorno).

Para usar la app mobile contra este backend: `python manage.py runserver 0.0.0.0:8001` y seguir [`mobile/README.md`](mobile/README.md).

---

## Tests y calidad

```bash
pytest -q                        # suite completa, con coverage mínimo de 80 %
pytest apps/expenses/ -q         # una app
ruff check . && ruff format .    # lint y formato
pre-commit run --all-files       # los mismos hooks que corren en cada commit
```

| Métrica (2026-11-10) | Valor |
|---|---|
| Tests backend | 1272 (2 omitidos) |
| Coverage backend | 86,4 % (mínimo exigido: 80 %) |
| Tests mobile | 98 (`cd mobile && flutter test`) |

CI (`.github/workflows/ci.yml`) corre en cada push a `develop` y `main`: lint, tests, auditoría de dependencias (pip-audit y safety), `check --deploy` con migraciones al día, y build.

---

## Estructura

```text
control_gastos/
├── apps/
│   ├── api/                # API REST v1 para la app mobile (DRF + JWT)
│   ├── core/               # Mixins, utilidades, email (Brevo), versión y novedades
│   ├── users/              # Usuario propio, registro, login, verificación, reset
│   ├── categories/         # Categorías y jerarquía grupo → subcategoría
│   ├── expenses/           # Gastos e importación de resúmenes
│   ├── income/             # Ingresos
│   ├── recurring/          # Gastos fijos y cuotas
│   ├── recurring_income/   # Ingresos fijos
│   ├── savings/            # Metas de ahorro
│   ├── shared_expenses/    # Gastos compartidos
│   ├── reports/            # Dashboard web
│   ├── notifications/      # Push, recordatorios y alertas de gasto
│   └── budgets/            # Sin modelos (módulo eliminado, D-007)
├── config/settings/        # base.py, dev.py, prod.py
├── templates/, static/     # Web
├── mobile/                 # App Flutter
├── docs/                   # Documentación técnica
├── scripts/                # Backup/restore de la base y chequeos
├── .github/workflows/      # CI, deploy, smoke tests, recordatorios y backup
├── requirements/           # base, dev, prod
└── render.yaml             # Definición de servicios en Render
```

---

## Flujo de trabajo

- Se trabaja en `develop` y se pasa a `main` con fast-forward; cada push a `main` despliega (ver [`docs/OPERACION.md`](docs/OPERACION.md)).
- Commits con el formato `tipo(scope): descripción en español` (`feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`), explicando el porqué.
- **Versión web:** `APP_VERSION` en `apps/core/views.py`, con entrada en `WHATS_NEW` si el cambio es visible y en `CHANGELOG.md`.
- **Versión mobile:** `version` en `mobile/pubspec.yaml`.
- **Decisiones no obvias y deuda técnica:** en `docs/DECISIONS.md`.

---

## Licencia

Proyecto de uso privado.

## Autor

**Nicolás Kachuk** · [![GitHub](https://img.shields.io/badge/GitHub-Nicokac-blue?logo=github)](https://github.com/Nicokac)
