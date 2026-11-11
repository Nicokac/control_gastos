# Plan de Remoción Completa: Presupuestos

**Fecha:** 2026-03-29
**Estado:** ✅ Completado
**Rama de trabajo:** `feature/remove-budgets`

## Objetivo

Eliminar por completo la funcionalidad **Presupuestos** del proyecto, incluyendo código,
UI, integraciones, tests, documentación y persistencia asociada.

## Alcance

La remoción incluye:

- app `apps.budgets`
- rutas globales y locales del módulo
- templates y enlaces visibles al usuario
- bloque de presupuestos en dashboard
- configuración de perfil ligada a alertas de presupuesto
- fixtures y tests del módulo y sus integraciones
- referencias en README y documentación
- migración de base de datos para eliminar la tabla de presupuestos

La remoción no incluye:

- cambios funcionales en gastos, ingresos, ahorro o categorías fuera de lo necesario
  para desacoplarlos de Presupuestos
- rediseño visual del dashboard más allá de cerrar el hueco dejado por el bloque eliminado

## Impacto Esperado

Seguirá funcionando:

- autenticación y perfil de usuario
- categorías, gastos, ingresos
- ahorro y movimientos
- balance mensual, distribución de gastos, últimas transacciones

Desaparecerá:

- CRUD de presupuestos y detalle de presupuesto
- copiado mensual de presupuestos
- alertas y resumen de presupuesto en dashboard
- acceso lateral a Presupuestos
- configuración de umbral orientada a presupuesto

## Fases de Ejecución

### Fase 1 — Desacople visible

Quitar toda referencia visible a Presupuestos sin tocar todavía la estructura completa.

#### Estado: ✅ Completada

### Fase 2 — Remoción del backend del módulo

Eliminar el módulo `budgets` del proyecto.

#### Estado: ✅ Completada

### Fase 3 — Base de datos y migraciones

Cerrar la remoción a nivel persistencia.

Implementación: migración `apps/expenses/migrations/0011_drop_budget_table.py`
usando `DROP TABLE IF EXISTS budgets_budget` para no fallar en instalaciones limpias.

#### Estado: ✅ Completada

### Fase 4 — Tests y fixtures

Dejar la suite coherente con el nuevo producto.

#### Estado: ✅ Completada — suite en 571 tests pasando, 0 referencias a `Budget`.

### Fase 5 — Documentación y cierre

Alinear el repositorio con el producto real.

#### Estado: ✅ Completada

## Estado Final (2026-05-04)

Criterios de cierre — todos cumplidos:

- ✅ `apps.budgets` no existe en `INSTALLED_APPS`
- ✅ No existen rutas `budgets/`
- ✅ No existen templates `templates/budgets/`
- ✅ El dashboard no importa ni renderiza datos de presupuesto
- ✅ El perfil no muestra configuración de alertas de presupuesto
- ✅ No existe fixture `budget_factory`
- ✅ No quedan tests activos que importen `Budget`
- ✅ README y docs no anuncian la funcionalidad
- ✅ Migración `0011_drop_budget_table` aplicada correctamente
- ✅ Suite completa pasa (571 tests, 93.38% coverage)
