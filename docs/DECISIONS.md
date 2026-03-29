# Decisiones de Diseño

Este documento registra decisiones técnicas y de producto tomadas conscientemente,
junto con su justificación. El objetivo es evitar que futuras auditorías las marquen
como issues pendientes.

---

## D-001 — amount_ars calculado en Python (no GeneratedField)

**Issue relacionada:** H-004  
**Fecha:** 2026-03-08  
**Estado:** ✅ Decisión tomada

### Contexto
`amount_ars` es un campo calculado en `CurrencyMixin.save()` que convierte el monto
original a ARS usando el `exchange_rate`. Django 5.x introdujo `GeneratedField` que
permitiría calcularlo directamente en la DB.

### Decisión
Mantener el cálculo en Python via `CurrencyMixin._calculate_amount_ars()`.

### Justificación
- El proyecto no usa `bulk_update()` ni `QuerySet.update()` en ningún path de negocio.
- La migración a `GeneratedField` requeriría un refactor profundo de `CurrencyMixin`,
  nuevas migraciones, y cambios en tests.
- El riesgo de desincronización es teórico en el contexto actual del proyecto.

### Riesgo aceptado
Si en el futuro se introduce `bulk_update()` o `bulk_create()` sin pasar por `save()`,
`amount_ars` podría quedar desincronizado. Mitigación: documentar en cada uso de
bulk ops que deben recalcular `amount_ars` manualmente.

---

## D-002 — expense_type y payment_method visibles en formulario de gastos

**Issue relacionada:** EX-003  
**Fecha:** 2026-03-08  
**Estado:** ✅ Decisión tomada

### Contexto
`expense_type` (Fijo/Variable) y `payment_method` (Efectivo/Débito/Crédito/Transferencia)
son campos opcionales en el formulario de gastos. La auditoría sugirió moverlos a una
sección colapsada por ser de "power user".

### Decisión
Mantenerlos visibles en el formulario principal.

### Justificación
- Ya existe un resumen colapsable en `expense_list` que muestra subtotales por tipo y método.
- Ya existen filtros en `expense_list` que los usan.
- El valor analítico justifica su presencia: permiten segmentar gastos fijos vs variables
  y analizar comportamiento por método de pago.
- Moverlos a sección colapsada reduciría su adopción sin beneficio real de UX.

---

## D-003 — alert_threshold global definido en User, no en Budget

**Issue relacionada:** EX-004  
**Fecha:** 2026-03-08  
**Estado:** ✅ Implementado (Fase 17 — tarea 17-10)

### Contexto
`alert_threshold` existe tanto en `User.profile` (global) como en cada `Budget`
(por presupuesto). La auditoría detectó ambigüedad sobre cuál prevalece.

### Decisión
El `alert_threshold` del `User` es el valor global por defecto. El de cada `Budget`
es un override por presupuesto. Si `Budget.alert_threshold` está en su valor default,
se usa el del `User`.

### Implementación
`BudgetForm.__init__()` usa `user.alert_threshold` como valor inicial del campo,
permitiendo al usuario sobreescribirlo por presupuesto. El `Budget.alert_threshold`
almacena el valor efectivo para ese presupuesto específico.

---

## D-004 — healthz sin rate limiting

**Issue relacionada:** H-007  
**Fecha:** 2026-03-08  
**Estado:** ⏳ Pendiente investigación (Fase 17 — tarea 17-7)

### Contexto
`/healthz/` es una ruta pública que ejecuta una query a la DB en cada request.
Sin rate limiting, podría usarse para amplificar carga sobre la DB.

### Pendiente
Evaluar si Render Free o el proxy ya aplica rate limiting externo antes de llegar
a Django. Si no, agregar throttling simple con `django-axes` o un decorator propio.

## D-005 — healthz devuelve 503 cuando la DB no está disponible

**Issue relacionada:** H-003, H-007  
**Fecha:** 2026-03-08  
**Estado:** ✅ Decisión tomada

### Contexto
Se detectaron 11 errores 503 en `logs/error.log` para `/healthz/` el 2026-03-07.
La auditoría los marcó como problema a investigar.

### Conclusión
El comportamiento es correcto. Los 503 ocurren cuando la DB no está disponible
(cold start de Render Free, o durante `flush` de DB en desarrollo). El endpoint
captura la excepción y retorna 503 con el mensaje de error — exactamente lo esperado.

### Decisión
No se agrega rate limiting a `/healthz/`. El endpoint es liviano (1 query),
Render Free aplica rate limiting externo, y agregar throttling añadiría
complejidad sin beneficio real en el contexto actual.

### Riesgo aceptado
En teoría un atacante podría usar `/healthz/` para amplificar carga sobre la DB.
En la práctica, el Free tier de Render limita el tráfico entrante antes de llegar
a Django.

## D-006 — CategoryListView no extiende UserOwnedListView

**Issue relacionada:** RE-003  
**Fecha:** 2026-03-08  
**Estado:** ✅ Decisión tomada

### Contexto
La auditoría sugirió que `CategoryListView` debería extender `UserOwnedListView`
del core para consistencia. `UserOwnedListView` aplica `UserOwnedQuerysetMixin`
que filtra automáticamente por `user=request.user`.

### Decisión
Mantener `CategoryListView` con `LoginRequiredMixin` + `ListView` directamente.

### Justificación
- `CategoryListView.get_queryset()` incluye categorías del sistema (sin usuario)
  además de las del usuario — `UserOwnedQuerysetMixin` sobreescribiría este comportamiento.
- `CategoryUpdateView` y `CategoryDeleteView` tienen su propio `get_queryset()`
  que filtra por `user` y `is_system=False` — lógica específica que no encaja
  en el mixin base.
- Forzar la herencia introduciría complejidad (override de get_queryset en subclase)
  sin beneficio real de DRY.

---

## D-007 â€” EliminaciÃ³n completa del mÃ³dulo de Presupuestos

**Issue relacionada:** PRD-REMOVE-BUDGETS  
**Fecha:** 2026-03-29  
**Estado:** â³ Aprobado para ejecuciÃ³n

### Contexto
El producto hoy incluye un mÃ³dulo completo de presupuestos mensuales por categorÃ­a
(`apps.budgets`) con integraciÃ³n en dashboard, navegaciÃ³n lateral, perfil de usuario
y suite de tests. Se decidiÃ³ remover la funcionalidad por completo.

### DecisiÃ³n
Eliminar el bloque de Presupuestos de manera total, incluyendo:
- app Django `apps.budgets`
- rutas, vistas, formularios, admin y templates del mÃ³dulo
- integraciÃ³n en dashboard y navegaciÃ³n
- referencias de perfil ligadas a alertas de presupuesto
- fixtures, tests, documentaciÃ³n y roadmap asociados

### JustificaciÃ³n
- El mÃ³dulo no es estructural para el registro de gastos, ingresos, ahorro o categorÃ­as.
- No existen otros modelos que dependan de `Budget` mediante claves forÃ¡neas entrantes.
- El mayor acoplamiento es de UI, reportes y tests, lo que permite una remociÃ³n controlada
  sin rediseÃ±ar el dominio principal.

### EjecuciÃ³n
El plan operativo detallado, con orden de trabajo y archivos alcanzados, queda documentado en:

`docs/REMOVE_BUDGETS_PLAN.md`
