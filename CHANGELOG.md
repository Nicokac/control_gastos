# Changelog

Todas las versiones notables de este proyecto están documentadas aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [0.12.0] — 2026-05-09

### Changed

- **Categorías — selector de color visual** — reemplazado `input[type=color]` nativo del browser por grilla de 10 círculos predefinidos (igual que Ahorro). Paleta definida en `CATEGORY_COLOR_CHOICES` en `constants.py`. El color se pre-carga correctamente al editar.
- **Categorías — copy del botón** — "Nuevo Grupo" renombrado a "Nueva Categoría" para que coincida con el formulario al que lleva.

---

## [0.11.0] — 2026-05-09

### Fixed

- **Ingresos — total del período mostraba $0** — el contexto usaba `total_amount` pero el template leía `total`. Renombrado.
- **Ingresos — categorías vacías en formularios y listado** — `get_income_categories` filtraba solo subcategorías (`parent__isnull=False`), pero las categorías de ingreso del sistema son de un solo nivel. Ahora retorna todas las INCOME sin restricción de parent.
- **Categorías de ingreso no visibles en `/categories/`** — `_build_full_tree` excluía grupos del sistema sin subcategorías. Corregido incluyendo todos los grupos.
- **Ahorro — monto objetivo vacío al editar** — `SavingForm` no vinculaba `target_amount` desde la instancia al ser un campo fuera de `Meta`. Corregido seteando `initial` en `__init__`.
- **Ahorro — color sin pre-seleccionar al editar** — `icon` y `color` son `ChoiceField` declarados fuera de `Meta`; Django no los vincula automáticamente. Corregido en `__init__`.
- **Ahorro — copy "Antes de crearla" en modo edición** — corregido con `{% if is_edit %}`.

---

## [0.10.0] — 2026-05-09

### Fixed

- **Monto vacío al editar gasto/ingreso** — `CurrencyFormMixin` reemplazaba el campo `amount` con `ARSDecimalField` sin preservar el valor de la instancia, dejando el campo vacío en edición. Corregido pasando `instance.amount` como `initial` al nuevo campo.
- **Resumen sin "Sin clasificar"** — el panel "Ver resumen" ignoraba los gastos sin tipo/método asignado. Ahora incluye una fila "Sin clasificar" con el monto restante cuando corresponde.

---

## [0.9.0] — 2026-05-09

### Added

- **Sidebar mobile** — en pantallas pequeñas el sidebar se abre como offcanvas (Bootstrap) desde un botón hamburguesa en el navbar. Comparte la misma navegación que el sidebar desktop via partial `sidebar_nav.html`.
- **Rate limiting en `/healthz/`** — throttle en memoria: máx 10 requests por IP en ventana de 60 segundos, retorna HTTP 429. Sin dependencias extra (D-004).

---

## [0.8.0] — 2026-05-09

### Added

- **Sidebar colapsable** — botón "Contraer/Expandir" que reduce el sidebar a íconos (64px). Estado persistido en `localStorage`. Animación CSS suave (`transition: width/margin-left 0.2s`).

### Fixed

- **Layout sin overflow horizontal** — reemplazado `container-fluid > row` por `div.app-layout` con `display: flex`. El `main` usa `flex: 1 + min-width: 0` en lugar de heredar `100vw` del grid de Bootstrap, eliminando el scroll horizontal espurio.
- **Responsive del main al colapsar sidebar** — el área de contenido ahora se expande correctamente cuando el sidebar se colapsa (64px) y se contrae cuando se expande (280px), en desktop. En mobile el sidebar pasa a `position: relative` y el main ocupa el ancho completo.

---

## [0.7.0] — 2026-05-09

### Corregido

- **Feedback via Resend API HTTP** — el envío de email del formulario de feedback fallaba en Render Free tier porque bloquea conexiones SMTP salientes (puertos 25, 465, 587). Migrado de `send_mail()` a `resend.Emails.send()` via API HTTP (puerto 443). Dependencia `resend` agregada a `requirements/prod.txt`.
- **Cambio de día a las 21hs** — reemplazado `timezone.now().date()` por `timezone.localdate()` en vistas, formularios, utils y modelos. La app ahora usa la fecha local de Argentina (UTC-3) en lugar de UTC.

---

## [0.6.0] — 2026-05-08

### Added
- **Jerarquía de categorías** — modelo grupo → subcategoría con FK self (`parent`). Los gastos se asignan a subcategorías; los grupos son agrupadores visuales (Fases 1–5).
- **Selector agrupado en formularios** — radio buttons de categorías agrupados bajo cabecera de grupo en formularios de gastos e ingresos (Fase 2).
- **Dashboard drill-down** — ranking de categorías expandible por grupo para ver desglose por subcategoría. Donut agrupado por grupo padre (Fase 3).
- **Filtro por grupo en lista de gastos** — selector de grupo + selector dinámico de subcategoría (JS con `data-parent`). La subcategoría tiene prioridad sobre el grupo al filtrar (Fase 4).
- **Mover subcategorías entre grupos** — campo `parent` visible al editar subcategorías; `?parent=<pk>` pre-selecciona el grupo en creación (Fase 5).

### Fixed
- **Constraint de unicidad de categorías** — reemplazada constraint `(name, user, type)` por dos constraints condicionales: una para grupos (`parent IS NULL`) y otra para subcategorías (`parent IS NOT NULL`), permitiendo nombres iguales en grupos y subcategorías distintas.
- **Cambio de día a las 21hs** — reemplazado `timezone.now().date()` por `timezone.localdate()` en todas las vistas, formularios y utils. La app ahora usa la fecha local de Argentina (UTC-3) en lugar de UTC.

### Changed
- "Ranking de Grupos" renombrado a "Ranking de Categorías" en el dashboard.
- Dashboard: distribución de gastos ahora agrupa por grupo padre con fallback a subcategoría para categorías sin jerarquía.

---

## [0.5.0] — 2026-05-04

### Added
- **Formulario de feedback** — sección "Reportar / Sugerir" en el sidebar. Envía email al administrador con tipo de reporte, mensaje y datos del usuario. Implementado en `apps.core` sin modelo de DB (D-010).
- **Gráfico de evolución mensual** — línea con 4 series (Ingresos, Gastos, Ahorro, Balance) desde enero hasta el mes actual. Balance con línea punteada (D-008).
- **Dashboard rediseñado** — Balance como card hero con barra de progreso y comparación porcentual vs mes anterior. Donut + ranking de categorías con scroll.
- **Picker visual de íconos** — selector de íconos con radio buttons en formularios de categorías y metas de ahorro.
- **Filtros avanzados de gastos** — filtro por método de pago y tipo de gasto (fijo/variable) con resumen colapsable.
- **Vinculación gasto → meta de ahorro** — al registrar un gasto se puede seleccionar una meta como destino; el monto se deposita automáticamente.
- **Formato ARS en campos de monto** — acepta coma como separador decimal en formularios.

### Fixed
- CSP: habilitado `unsafe-inline` en `style-src` para styles dinámicos del dashboard (D-009).
- Barra de progreso del balance usa clases Bootstrap en lugar de inline color.
- `format_currency()` centralizado en filtro de template.

---

## [0.4.0] — 2026-03-29

### Removed
- **Módulo de presupuestos** (`apps.budgets`) eliminado por completo — vistas, formularios, admin, templates, fixtures, tests y referencias en dashboard/sidebar/perfil (D-007).

---

## [0.3.0] — 2026-03-08

### Added
- **Rate limiting** con django-axes: 5 intentos fallidos → bloqueo 2 horas. Página `account_locked` dedicada.
- **Headers de seguridad** — HSTS, CSP, X-Frame-Options, SESSION/CSRF cookies seguras en prod.
- **Logging estructurado** — eventos de seguridad, performance (RequestTimingMiddleware) y errores.
- **Error tracking** con Sentry (prod).
- **Comando `generate_secret_key`** — genera SECRET_KEY segura con opción `--env-format`.
- **Comando `axes_status`** — muestra y limpia intentos de login fallidos.
- **Comando `view_logs`** — consulta logs por tipo (security, error, app).
- **Healthcheck** `/healthz/` — verifica DB y retorna 200/503.
- **Índices compuestos** en Expense, Income, Saving, Category para queries frecuentes.
- **Constraints de DB** en Category: `system_category_no_user`, `user_category_requires_user`.

### Fixed
- `alert_threshold` del User se usa como default en cada Budget (D-003).
- Income: unificado filtrado de fechas con `get_month_date_range_exclusive`.
- Login redirige al dashboard en lugar de categories.
- Eliminado `MEDIA_ROOT` sin definir y comentarios muertos.

### Changed
- Sidebar: "Configuración" → "Mi cuenta".
- "Nuevo Gasto" estandarizado en toda la UI.

---

## [0.2.0] — 2026-02-17

### Added
- **Metas de ahorro** (`apps.savings`) — crear metas con objetivo y fecha límite, registrar depósitos y retiros, seguimiento de progreso porcentual, auto-completado al llegar al objetivo.
- **Multimoneda** — soporte ARS/USD con tipo de cambio configurable. `amount_ars` calculado en Python via `CurrencyMixin.save()` (D-001).
- **Dashboard** — balance mensual, comparación con mes anterior, últimas transacciones, distribución de gastos por categoría.
- **Categorías personalizadas** — CRUD de categorías por usuario, iconos y colores, tipos Gasto/Ingreso.
- **Paginación** en listados de gastos, ingresos y metas.
- **CI/CD** con GitHub Actions — lint, tests, coverage ≥80%, security checks, django-checks, collectstatic, deploy a Render.
- **Pre-commit hooks** — Ruff, ruff-format, detect-secrets, validaciones de whitespace.
- **Scripts de backup** (`backup_db.ps1`, `restore_db.ps1`) para uso futuro con acceso externo a PostgreSQL.

### Changed
- Arquitectura: mixins unificados en `core/views.py` (`UserOwnedListView`, `UserOwnedCreateView`, etc.).
- Separación de settings en `base.py`, `dev.py`, `prod.py`.

---

## [0.1.0] — 2026-01-15

### Added
- Proyecto inicial Django 5.2 / Python 3.12.
- Autenticación — registro, login, logout, perfil de usuario.
- CRUD de gastos con fecha, descripción, monto y categoría.
- CRUD de ingresos.
- Categorías de sistema predefinidas (`seed_categories`).
- Deploy inicial a Render (Free tier) con PostgreSQL.
- SQLite en desarrollo, PostgreSQL en producción.
