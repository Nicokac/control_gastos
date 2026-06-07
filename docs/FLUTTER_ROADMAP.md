# Roadmap: App Móvil Flutter — Control de Gastos

Documento de trazabilidad para el desarrollo de la app mobile.  
Cada fase se tilda al completarse. Las subtareas se marcan con ✅ al cerrar.

---

## Estado Actual

- ✅ Backend Django completo (web app funcional en producción — v1.8.0)
- ✅ API REST completa (DRF + JWT, todos los endpoints)
- ✅ App Flutter en progreso — Auth, Dashboard, Gastos, Ingresos, Gastos Compartidos funcionando

---

## FASE 0 — Preparar el Backend para API
**Estado:** ✅ Completa (2026-06-04)

### 0.1 Instalar y configurar DRF + JWT
- [x] Instalar `djangorestframework`, `djangorestframework-simplejwt`, `django-cors-headers`
- [x] Configurar `REST_FRAMEWORK` con autenticación JWT en settings
- [x] Configurar `CORS_ALLOWED_ORIGINS` para Flutter en desarrollo
- [x] Agregar a `INSTALLED_APPS`: `rest_framework`, `corsheaders`

### 0.2 Endpoints de Auth
- [x] `POST /api/v1/auth/token/` — obtener access + refresh token
- [x] `POST /api/v1/auth/token/refresh/` — renovar access token
- [x] `POST /api/v1/auth/register/` — crear cuenta
- [x] `GET  /api/v1/auth/me/` — perfil del usuario autenticado
- [x] `PUT  /api/v1/auth/me/` — actualizar perfil

### 0.3 Endpoints base
- [x] `CategoryViewSet` — CRUD, solo propias + sistema
- [x] `ExpenseViewSet` — CRUD, filtros mes/año/categoría
- [x] `IncomeViewSet` — CRUD, filtros mes/año
- [x] `SavingViewSet` — CRUD + depósitos/retiros

### 0.4 Tests de Fase 0
- [x] `apps/api/tests/test_auth.py`
- [x] `apps/api/tests/test_categories.py`
- [x] `apps/api/tests/test_expenses.py`
- [x] `apps/api/tests/test_income.py`
- [x] `apps/api/tests/test_savings.py`

---

## FASE 1 — Completar API REST
**Estado:** ✅ Completa (2026-06-04)

### 1.1 Endpoints de Gastos Recurrentes
- [x] `RecurringExpenseSerializer` — nota: el modelo no tiene `amount`, se deriva de `last_expense`
- [x] `RecurringExpenseViewSet` — CRUD
- [x] Action `mark_paid` — crea un `Expense` vinculado
- [x] Action `pending` — lista pendientes del mes actual
- [x] Registrar en `urls.py`

### 1.2 Endpoints de Ingresos Recurrentes
- [x] `RecurringIncomeSerializer`
- [x] `RecurringIncomeViewSet` — CRUD
- [x] Action `mark_received` — crea un `Income` vinculado
- [x] Action `pending` — lista pendientes del mes actual
- [x] Registrar en `urls.py`

### 1.3 Endpoints de Gastos Compartidos
- [x] `SharedExpenseSerializer`
- [x] `HouseholdMemberSerializer`
- [x] `SharedExpenseViewSet` — CRUD
- [x] `HouseholdMemberViewSet` — CRUD
- [x] Registrar en `urls.py`

### 1.4 Endpoint de Dashboard
- [x] `DashboardView` (APIView) — `GET /api/v1/dashboard/?month=6&year=2026`
- [x] Response incluye: `total_expenses`, `total_income`, `balance`, `expenses_by_category`, `income_by_category`, `savings_progress`, `pending_recurring`, `recent_transactions`

### 1.5 Tests de Fase 1
- [x] `apps/api/tests/test_recurring.py`
- [x] `apps/api/tests/test_recurring_income.py`
- [x] `apps/api/tests/test_shared_expenses.py`
- [x] `apps/api/tests/test_dashboard.py`

### 1.6 Documentación API
- [x] Instalar `drf-spectacular`
- [x] Configurar `DEFAULT_SCHEMA_CLASS` en settings
- [x] Exponer `GET /api/schema/` y `GET /api/docs/` (Swagger UI)

---

## FASE 2 — Setup Proyecto Flutter
**Estado:** ✅ Completa (2026-06-04)

### 2.1 Crear proyecto
- [x] `flutter create --org com.tudominio control_gastos_app`

### 2.2 Dependencias (pubspec.yaml)
- [x] `flutter_riverpod`, `riverpod_annotation`
- [x] `dio`
- [x] `flutter_secure_storage`, `shared_preferences`
- [x] `go_router`
- [x] `intl`
- [x] `freezed_annotation`, `json_annotation`
- [x] Dev: `build_runner`, `freezed`, `json_serializable`, `riverpod_generator`

### 2.3 Estructura de carpetas
- [x] Crear estructura `lib/` con `core/`, `data/`, `features/`, `routing/`
- [x] Features: `auth`, `dashboard`, `expenses`, `income`, `shared_expenses`

---

## FASE 3 — Implementar Core Flutter
**Estado:** ✅ Completa (2026-06-04)

### 3.1 Configuración de API
- [x] `api_service.dart` con Dio + interceptors (Bearer token, refresh automático)

### 3.2 Repositorios
- [x] `auth_repository.dart`
- [x] `expense_repository.dart`
- [x] `income_repository.dart`
- [x] `shared_expense_repository.dart`
- [x] `dashboard_repository.dart`

### 3.3 Providers con Riverpod
- [x] `auth_provider.dart`
- [x] `expense_provider.dart`
- [x] `income_provider.dart`
- [x] `shared_expense_provider.dart`
- [x] `dashboard_provider.dart`

### 3.4 Router
- [x] `app_router.dart` con GoRouter
- [x] Redirect a `/login` si no autenticado
- [x] Rutas: `/splash`, `/login`, `/register`, `/dashboard`, `/expenses`, `/income`, `/shared-expenses`
- [x] Helper `formatters.dart` para montos ARS

---

## FASE 4 — Implementar Features Flutter
**Estado:** ✅ Completa (MVP — 2026-06-05)

### 4.1 Auth
- [x] `splash_screen.dart` (check token, redirect)
- [x] `login_screen.dart`
- [x] `register_screen.dart`

### 4.2 Dashboard
- [x] `dashboard_screen.dart`
- [x] Widget `balance_card.dart`
- [x] Widget `expense_chart.dart` (pie chart por categoría)
- [x] Widget `recent_transactions_list.dart`
- [x] Widget `pending_recurring_card.dart`

### 4.3 Expenses
- [x] `expense_list_screen.dart` (con filtros mes/año)
- [x] `expense_form_screen.dart` (crear/editar)
- [x] Widget `expense_tile.dart`
- [x] Widget `category_selector.dart` (reemplazado por bottom sheets anidados)

### 4.4 Income
- [x] `income_list_screen.dart`
- [x] `income_form_screen.dart`
- [x] Widget `income_tile.dart`

### 4.5 Shared Expenses
- [x] `shared_expense_list_screen.dart` (filtros mes/año, totales por persona)
- [x] `shared_expense_form_screen.dart` (crear/editar — quién pagó)
- [x] `household_members_screen.dart` (ver, agregar, eliminar miembros)
- [x] Widget `shared_expense_tile.dart`

### 4.6 Categories
- [x] `categories_screen.dart` (lista agrupada por tipo y grupo)
- [x] Crear grupo y subcategoría con selector de color
- [x] Eliminar subcategorías propias (protege las del sistema)

### 4.7 Savings
- [x] `savings_list_screen.dart` (cards con progreso, depósito/retiro/editar/eliminar)
- [x] `saving_detail_screen.dart` (resumen + historial de movimientos)
- [x] `saving_form_screen.dart` (crear/editar, selector de ícono y color)
- [x] Card de meta con progress bar (`_SavingCard`, inline en la lista)
- [x] Diálogos de depósito/retiro (`_showMovementDialog`, inline en la lista)

### 4.8 Recurring (Gastos Fijos)
- [x] `recurring_list_screen.dart` (con estados pagado/pendiente/vencido)
- [x] `recurring_form_screen.dart` (crear/editar)
- [x] Action "Marcar como pagado" desde la lista (menú contextual)

### 4.9 Settings
- [x] `settings_screen.dart`
- [x] Editar perfil, moneda default, día inicio mes, cerrar sesión

### 4.10 Acerca de
- [x] `about_screen.dart` — versión de la app, sitio web, desarrollador y contacto por email
- [x] Acceso desde Settings (`ListTile` en sección "Información")
- [x] Web: tarjeta "Acerca de" en `templates/users/profile.html` con la misma información

---

## FASE 5 — Polish y Release
**Estado:** ✅ Completada

### 5.1 UI/UX
- [x] Tema claro/oscuro con persistencia (SegmentedButton en Settings)
- [x] Animaciones de transición entre pantallas (fade + slide suave via GoRouter)
- [x] Pull to refresh en listas (RefreshIndicator en todas las pantallas)
- [x] Empty states con ícono, subtítulo y acción (widget EmptyState reutilizable)
- [x] Skeleton loaders en dashboard (DashboardSkeleton con animación pulse)
- [x] Dashboard optimizado: balance card con totales tocables, recurrentes compactos con progreso, accesos directos a Compartidos y Categorías

### 5.2 Offline Support
- [ ] Cache local con Hive
- [ ] Sincronización al reconectar
- [ ] Indicador visual de modo offline

### 5.3 Build & Release
- [ ] `flutter build apk --release`
- [ ] `flutter build appbundle --release`
- [ ] Android: Google Play Console

---

## FASE 6 — Testing
**Estado:** ✅ Completa (2026-06-07) — 51 tests pasando

### 6.1 Unit Tests
- [x] `auth_provider` — login exitoso, login fallido, logout
- [x] `dashboard_provider` — carga de datos, cambio de mes, reload
- [x] `expense_provider` — CRUD, filtros por mes
- [x] `recurring_provider` — marcar pagado, revertir pago, estados, delete

### 6.2 Widget Tests
- [x] `BalanceCard` — valores positivos y negativos, callbacks
- [x] `EmptyState` — con y sin acción, con y sin subtítulo
- [x] `PendingRecurringCard` — con pendientes, todos pagados, vencidos
- [x] `DashboardSkeleton` — renderiza sin errores
- [x] `LoginScreen` — validación de campos, toggle contraseña, contenido

### 6.3 Integration Tests
- [ ] Flujo auth: login → dashboard → logout (pendiente — requiere entorno de staging)

---

## FASE 7 — v2 Features
**Estado:** ⏳ Pendiente

### 7.1 Mejoras pendientes (deuda técnica)
- [x] DT-048 — ícono representativo de la app
- [x] DT-049 — deshacer "marcar pagado" en gastos fijos

---

## Estimación de tiempo

| Fase | Descripción | Estimado |
|---|---|---|
| 0 | Preparar backend (DRF + JWT + endpoints base) | 4-6 hs |
| 1 | Completar API (recurring, dashboard, docs) | 3-4 hs |
| 2 | Setup Flutter | 1 hs |
| 3 | Core (API, models, routing) | 4-5 hs |
| 4 | Features (todas las pantallas) | 16-20 hs |
| 5 | Polish & release | 6-8 hs |
| **Total** | | **34-44 hs** |

---

## Registro de progreso

| Fecha | Fase | Tarea completada |
|---|---|---|
| 2026-06-04 | Fase 0 | DRF + JWT + CORS instalados y configurados |
| 2026-06-04 | Fase 0 | Endpoints auth: token, refresh, register, me |
| 2026-06-04 | Fase 0 | Endpoints base: categories, expenses, income, savings |
| 2026-06-04 | Fase 0 | 40 tests pasando (auth, categories, expenses, income, savings) |
| 2026-06-04 | Fase 1 | Endpoints recurring, recurring-income, shared-expenses, household-members, dashboard |
| 2026-06-04 | Fase 1 | drf-spectacular instalado — Swagger UI en /api/v1/docs/ |
| 2026-06-04 | Fase 1 | 68 tests pasando en total (28 nuevos) |
| 2026-06-04 | Fase 2 | Proyecto Flutter creado en mobile/, dependencias instaladas |
| 2026-06-04 | Fase 3 | API service, auth repository, router, splash/login/register/dashboard screens |
| 2026-06-04 | Fase 3 | Login screen funcionando en emulador Android (API 37) |
| 2026-06-04 | Fase 4 | Dashboard completo: balance, pie chart, recurrentes pendientes, últimos movimientos |
| 2026-06-04 | Fase 4 | Expenses: lista con filtros, formulario crear/editar/eliminar con bottom sheets de categoría |
| 2026-06-04 | Fase 4 | Income: lista con filtros, formulario crear/editar/eliminar |
| 2026-06-04 | Fase 4 | Dashboard invalida automáticamente al mutar gastos o ingresos |
| 2026-06-05 | Fase 4 | Shared Expenses: lista con totales por persona, form crear/editar, miembros del hogar |
| 2026-06-05 | Fase 4 | Colores alineados con web: danger=gastos, success=ingresos, primary=#0d6efd=compartidos |
| 2026-06-05 | Fase 4 | Settings: editar perfil, moneda, día de inicio, cerrar sesión |
| 2026-06-06 | Fase 4 | Categories: lista agrupada, crear grupos/subcategorías, eliminar propias |
| 2026-06-06 | Fase 5 | Empty states con widget reutilizable en todas las pantallas |
| 2026-06-06 | Fase 5 | Dashboard: balance tocable, recurrentes compactos con progreso, botones Compartidos y Categorías |
| 2026-06-06 | Fase 4 | Recurring (Gastos Fijos): lista con estados pagado/pendiente/vencido, form crear/editar, acción "Marcar como pagado" — verificado completo, roadmap actualizado |
| 2026-06-06 | Fix | AndroidManifest: permiso INTERNET agregado — APK release puede hacer requests de red |
| 2026-06-06 | Fase 4 | Recurring (Gastos Fijos): lista, formulario, marcar pagado, editar, eliminar |
| 2026-06-06 | Fase 4 | Savings: lista con cards de progreso, detalle con historial de movimientos, form con selector de ícono/color, depósito/retiro/editar/eliminar, acceso desde dashboard |
| 2026-06-06 | Fase 5 | Tema claro/oscuro con persistencia en SharedPreferences |
| 2026-06-06 | Fase 5 | Animaciones de transición: fade + slide en todas las rutas |
| 2026-06-06 | Fase 5 | Skeleton loaders en dashboard |
| 2026-06-06 | Fase 6 | Definida fase de testing: unit, widget e integration tests |
| 2026-06-06 | Fase 5 | Dashboard: indicador "Actualizado hace X minutos" + confirmación al refrescar |
| 2026-06-06 | Fase 5 | Formularios de gasto/ingreso rediseñados: monto destacado, íconos, secciones, color de categoría |
| 2026-06-06 | Fix | API categorías: page_size ignorado truncaba el listado a 50 — agregada paginación configurable |
| 2026-06-06 | Fase 4 | Acerca de: pantalla móvil propia (versión, sitio web, desarrollador, contacto) accesible desde Settings + tarjeta equivalente en "Mi perfil" en la web |
