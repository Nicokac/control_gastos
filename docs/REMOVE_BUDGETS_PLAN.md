# Plan de RemociÃ³n Completa: Presupuestos

**Fecha:** 2026-03-29  
**Estado:** Plan aprobado, implementaciÃ³n pendiente  
**Rama de trabajo:** `feature/remove-budgets`

## Objetivo

Eliminar por completo la funcionalidad **Presupuestos** del proyecto, incluyendo cÃ³digo,
UI, integraciones, tests, documentaciÃ³n y persistencia asociada.

## Alcance

La remociÃ³n incluye:
- app `apps.budgets`
- rutas globales y locales del mÃ³dulo
- templates y enlaces visibles al usuario
- bloque de presupuestos en dashboard
- configuraciÃ³n de perfil ligada a alertas de presupuesto
- fixtures y tests del mÃ³dulo y sus integraciones
- referencias en README y documentaciÃ³n
- migraciÃ³n de base de datos para eliminar la tabla de presupuestos

La remociÃ³n no incluye:
- cambios funcionales en gastos, ingresos, ahorro o categorÃ­as fuera de lo necesario
  para desacoplarlos de Presupuestos
- rediseÃ±o visual del dashboard mÃ¡s allÃ¡ de cerrar el hueco dejado por el bloque eliminado

## Impacto Esperado

SeguirÃ¡ funcionando:
- autenticaciÃ³n y perfil de usuario
- categorÃ­as
- gastos
- ingresos
- ahorro y movimientos
- balance mensual
- distribuciÃ³n de gastos
- Ãºltimas transacciones

DesaparecerÃ¡:
- CRUD de presupuestos
- detalle de presupuesto
- copiado mensual de presupuestos
- alertas y resumen de presupuesto en dashboard
- acceso lateral a Presupuestos
- configuraciÃ³n de umbral orientada a presupuesto

## Roadmap de EjecuciÃ³n

### Fase 1 - Desacople visible

Objetivo: quitar toda referencia visible a Presupuestos sin tocar todavÃ­a la estructura completa.

Archivos objetivo:
- `templates/components/sidebar.html`
- `templates/reports/dashboard.html`
- `apps/reports/views.py`
- `apps/users/forms.py`
- `templates/users/profile.html`

Tareas:
- eliminar el enlace lateral a `budgets:list`
- quitar el bloque de presupuestos del dashboard
- remover imports y contexto de presupuesto en `DashboardView`
- eliminar del estado vacÃ­o del dashboard la menciÃ³n a Presupuestos
- quitar de perfil el campo/help text `alert_threshold` si queda sin uso

Resultado esperado:
- la UI no expone Presupuestos
- el dashboard no importa ni renderiza datos de `Budget`

### Fase 2 - RemociÃ³n del backend del mÃ³dulo

Objetivo: eliminar el mÃ³dulo `budgets` del proyecto.

Archivos objetivo:
- `config/settings/base.py`
- `config/urls.py`
- `apps/budgets/apps.py`
- `apps/budgets/admin.py`
- `apps/budgets/forms.py`
- `apps/budgets/models.py`
- `apps/budgets/urls.py`
- `apps/budgets/views.py`
- `templates/budgets/*`

Tareas:
- quitar `apps.budgets` de `INSTALLED_APPS`
- quitar `path("budgets/", include("apps.budgets.urls"))`
- eliminar app, templates y admin del mÃ³dulo

Resultado esperado:
- el proyecto no contiene cÃ³digo ejecutable de Presupuestos

### Fase 3 - Base de datos y migraciones

Objetivo: cerrar la remociÃ³n a nivel persistencia.

Archivos objetivo:
- nueva migraciÃ³n en la app correspondiente
- historial de migraciones de `apps/budgets`

Tareas:
- generar migraciÃ³n para eliminar la tabla/modelo `Budget`
- validar orden de dependencias de migraciÃ³n
- decidir si se conserva el historial de migraciones de la app o si se elimina la app
  dejando solo la migraciÃ³n de drop en una transiciÃ³n controlada

DecisiÃ³n recomendada:
- hacer la remociÃ³n en dos pasos de implementaciÃ³n real:
  1. quitar referencias activas y generar migraciÃ³n de borrado
  2. eliminar restos de la app cuando la DB ya no requiera cargar el modelo

Resultado esperado:
- la base de datos no mantiene estructura ni datos de presupuestos

### Fase 4 - Tests y fixtures

Objetivo: dejar la suite coherente con el nuevo producto.

Archivos objetivo:
- `conftest.py`
- `apps/budgets/tests/*`
- `apps/core/tests/integration/test_user_journey.py`
- `apps/core/tests/integration/test_expense_flow.py`
- `apps/core/tests/integration/test_dashboard_integration.py`
- `apps/core/tests/integration/test_error_handling.py`
- `apps/core/tests/integration/test_user_isolation.py`
- `apps/core/tests/test_views.py`
- `apps/reports/tests/test_views.py`

Tareas:
- eliminar `budget_factory` y fixture `budget`
- borrar tests propios de `budgets`
- reescribir tests de dashboard para validar el nuevo contenido
- eliminar journeys que dependan de crear presupuestos
- ajustar tests de error handling y aislamiento que usaban rutas o modelos de Presupuestos

Resultado esperado:
- la suite deja de asumir la existencia del mÃ³dulo

### Fase 5 - DocumentaciÃ³n y cierre

Objetivo: alinear el repositorio con el producto real.

Archivos objetivo:
- `README.md`
- `docs/DECISIONS.md`
- `docs/REMOVE_BUDGETS_PLAN.md`

Tareas:
- eliminar menciones a Presupuestos de descripciÃ³n, features, estructura y roadmap
- remover `budgets` del listado de apps y modelos principales
- dejar registrado que el bloque fue retirado por decisiÃ³n de producto

Resultado esperado:
- no quedan referencias engaÃ±osas a una funcionalidad inexistente

## Orden Exacto Recomendado de ImplementaciÃ³n

1. Quitar bloque visual del dashboard y sidebar.
2. Quitar lÃ³gica de presupuesto de `apps.reports.views`.
3. Quitar `alert_threshold` del perfil si ya no tiene sentido funcional.
4. Ajustar tests de dashboard y perfil.
5. Quitar rutas globales del mÃ³dulo.
6. Eliminar la app `apps.budgets` del cÃ³digo.
7. Generar y revisar migraciÃ³n de borrado de `Budget`.
8. Eliminar fixtures y tests ligados a Presupuestos.
9. Actualizar README y documentaciÃ³n.
10. Ejecutar suite y corregir regresiones.

## Riesgos

- Quitar la app antes de resolver migraciones puede impedir cargar el proyecto correctamente.
- Quitar solo templates o rutas sin tocar `apps.reports.views` rompe el dashboard por imports directos.
- Quitar `alert_threshold` del perfil exige revisar tests y posibles validaciones asociadas.
- La mayor parte del esfuerzo estÃ¡ en limpieza transversal, no en lÃ³gica de dominio.

## Criterios de Cierre

La remociÃ³n se considera completa cuando:
- no existe `apps.budgets` en `INSTALLED_APPS`
- no existen rutas `budgets/`
- no existen templates `templates/budgets/`
- el dashboard no importa ni renderiza datos de presupuesto
- el perfil no muestra configuraciÃ³n de alertas de presupuesto
- no existe fixture `budget_factory`
- no quedan tests activos que importen `Budget`
- README y docs no anuncian la funcionalidad
- las migraciones aplican correctamente
- la suite relevante pasa
