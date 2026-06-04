# Roadmap: App Móvil Flutter — Control de Gastos

Documento de trazabilidad para el desarrollo de la app mobile.  
Cada fase se tilda al completarse. Las subtareas se marcan con ✅ al cerrar.

---

## Estado Actual

- ✅ Backend Django completo (web app funcional en producción — v1.8.0)
- ❌ API REST no existe — hay que construirla desde cero
- ❌ App Flutter no existe

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
**Estado:** ⏳ Pendiente

### 1.1 Endpoints de Gastos Recurrentes
- [ ] `RecurringExpenseSerializer` — nota: el modelo no tiene `amount`, se deriva de `last_expense`
- [ ] `RecurringExpenseViewSet` — CRUD
- [ ] Action `mark_paid` — crea un `Expense` vinculado
- [ ] Action `pending` — lista pendientes del mes actual
- [ ] Registrar en `urls.py`

### 1.2 Endpoints de Ingresos Recurrentes
- [ ] `RecurringIncomeSerializer`
- [ ] `RecurringIncomeViewSet` — CRUD
- [ ] Action `mark_received` — crea un `Income` vinculado
- [ ] Action `pending` — lista pendientes del mes actual
- [ ] Registrar en `urls.py`

### 1.3 Endpoints de Gastos Compartidos
- [ ] `SharedExpenseSerializer`
- [ ] `HouseholdMemberSerializer`
- [ ] `SharedExpenseViewSet` — CRUD
- [ ] `HouseholdMemberViewSet` — CRUD
- [ ] Registrar en `urls.py`

### 1.4 Endpoint de Dashboard
- [ ] `DashboardView` (APIView) — `GET /api/v1/dashboard/?month=6&year=2026`
- [ ] Response incluye: `total_expenses`, `total_income`, `balance`, `expenses_by_category`, `income_by_category`, `savings_progress`, `pending_recurring`, `recent_transactions`

### 1.5 Tests de Fase 1
- [ ] `apps/api/tests/test_recurring.py`
- [ ] `apps/api/tests/test_recurring_income.py`
- [ ] `apps/api/tests/test_shared_expenses.py`
- [ ] `apps/api/tests/test_dashboard.py`

### 1.6 Documentación API
- [ ] Instalar `drf-spectacular`
- [ ] Configurar `DEFAULT_SCHEMA_CLASS` en settings
- [ ] Exponer `GET /api/schema/` y `GET /api/docs/` (Swagger UI)

---

## FASE 2 — Setup Proyecto Flutter
**Estado:** ⏳ Pendiente

### 2.1 Crear proyecto
- [ ] `flutter create --org com.tudominio control_gastos_app`

### 2.2 Dependencias (pubspec.yaml)
- [ ] `flutter_riverpod`, `riverpod_annotation`
- [ ] `dio`, `retrofit`
- [ ] `flutter_secure_storage`, `shared_preferences`
- [ ] `go_router`
- [ ] `intl`
- [ ] `freezed_annotation`, `json_annotation`
- [ ] `hive_flutter` (offline support)
- [ ] Dev: `build_runner`, `freezed`, `json_serializable`, `retrofit_generator`, `riverpod_generator`, `hive_generator`

### 2.3 Estructura de carpetas
- [ ] Crear estructura `lib/` con `core/`, `data/`, `features/`, `routing/`
- [ ] Features: `auth`, `dashboard`, `expenses`, `income`, `savings`, `recurring`, `settings`

---

## FASE 3 — Implementar Core Flutter
**Estado:** ⏳ Pendiente

### 3.1 Configuración de API
- [ ] `api_service.dart` con Dio + interceptors (Bearer token, refresh automático, manejo de errores, logging)

### 3.2 Modelos con Freezed
- [ ] `user.dart`
- [ ] `category.dart`
- [ ] `expense.dart`
- [ ] `income.dart`
- [ ] `saving.dart`
- [ ] `recurring_expense.dart`
- [ ] `api_response.dart` (wrapper genérico)
- [ ] Ejecutar `flutter pub run build_runner build`

### 3.3 Repositorios con Retrofit
- [ ] `auth_repository.dart`
- [ ] `category_repository.dart`
- [ ] `expense_repository.dart`
- [ ] `income_repository.dart`
- [ ] `saving_repository.dart`
- [ ] `recurring_repository.dart`
- [ ] Ejecutar `flutter pub run build_runner build`

### 3.4 Providers con Riverpod
- [ ] `auth_provider.dart`
- [ ] `expense_provider.dart`
- [ ] `income_provider.dart`
- [ ] `saving_provider.dart`
- [ ] `recurring_provider.dart`

### 3.5 Router
- [ ] `app_router.dart` con GoRouter
- [ ] Redirect a `/login` si no autenticado
- [ ] Rutas: `/login`, `/register`, `/dashboard`, `/expenses`, `/income`, `/savings`, `/recurring`, `/settings`
- [ ] Bottom navigation bar

---

## FASE 4 — Implementar Features Flutter
**Estado:** ⏳ Pendiente

### 4.1 Auth
- [ ] `splash_screen.dart` (check token, redirect)
- [ ] `login_screen.dart`
- [ ] `register_screen.dart`

### 4.2 Dashboard
- [ ] `dashboard_screen.dart`
- [ ] Widget `balance_card.dart`
- [ ] Widget `expense_chart.dart` (pie chart por categoría)
- [ ] Widget `recent_transactions_list.dart`
- [ ] Widget `pending_recurring_card.dart`

### 4.3 Expenses
- [ ] `expense_list_screen.dart` (con filtros mes/año)
- [ ] `expense_form_screen.dart` (crear/editar)
- [ ] Widget `expense_tile.dart`
- [ ] Widget `category_selector.dart` (grid visual)
- [ ] Widget `amount_input.dart` (con selector de moneda)

### 4.4 Income
- [ ] `income_list_screen.dart`
- [ ] `income_form_screen.dart`
- [ ] Widget `income_tile.dart`

### 4.5 Savings
- [ ] `savings_list_screen.dart`
- [ ] `saving_detail_screen.dart` (con historial de movimientos)
- [ ] `saving_form_screen.dart`
- [ ] Widget `saving_card.dart` (con progress bar)
- [ ] Widget `deposit_dialog.dart`
- [ ] Widget `withdraw_dialog.dart`

### 4.6 Recurring
- [ ] `recurring_list_screen.dart`
- [ ] `recurring_form_screen.dart`
- [ ] Widget `recurring_tile.dart` (con estado pagado/pendiente/vencido)

### 4.7 Settings
- [ ] `settings_screen.dart`
- [ ] Editar perfil, moneda default, día inicio mes, cerrar sesión

---

## FASE 5 — Polish y Release
**Estado:** ⏳ Pendiente

### 5.1 UI/UX
- [ ] Tema claro/oscuro
- [ ] Animaciones de transición entre pantallas
- [ ] Pull to refresh en listas
- [ ] Empty states con ilustraciones
- [ ] Skeleton loaders

### 5.2 Offline Support
- [ ] Cache local con Hive
- [ ] Sincronización al reconectar
- [ ] Indicador visual de modo offline

### 5.3 Testing
- [ ] Unit tests para providers
- [ ] Widget tests para componentes clave
- [ ] Integration tests para flujos principales (auth, crear gasto, ver dashboard)

### 5.4 Build & Release
- [ ] `flutter build apk --release`
- [ ] `flutter build appbundle --release`
- [ ] `flutter build ios --release`

### 5.5 Distribución
- [ ] Android: Google Play Console
- [ ] iOS: App Store Connect
- [ ] Beta: Firebase App Distribution

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
