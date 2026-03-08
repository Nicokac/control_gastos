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
**Estado:** ⏳ Pendiente implementación (Fase 17 — tarea 17-10)

### Contexto
`alert_threshold` existe tanto en `User.profile` (global) como en cada `Budget`
(por presupuesto). La auditoría detectó ambigüedad sobre cuál prevalece.

### Decisión
El `alert_threshold` del `User` es el valor global por defecto. El de cada `Budget`
es un override por presupuesto. Si `Budget.alert_threshold` está en su valor default,
se usa el del `User`.

### Pendiente
Verificar que la lógica de negocio en `Budget` implemente correctamente esta jerarquía
y documentarlo en el código.

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
