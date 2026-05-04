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

## D-008 — Evolución mensual: enero → mes actual (no 12 meses fijos)

**Fecha:** 2026-05-03
**Estado:** ✅ Decisión tomada

### Contexto
El gráfico de evolución mensual en el dashboard necesitaba definir su rango de tiempo.
Las opciones eran: últimos N meses, año completo (12 meses fijos), o enero → mes actual.

### Decisión
Mostrar desde enero del año en curso hasta el mes actual inclusive.
El rango crece mes a mes: en Mayo muestra Ene–May, en Junio muestra Ene–Jun, etc.

### Justificación
- Refleja el año fiscal natural del usuario sin mostrar meses futuros vacíos.
- Evita lógica compleja de "últimos N meses" que cruza años.
- 3 queries fijas (Expense, Income, SavingMovement) independientemente del mes actual.
- Cada query usa agregación por mes en DB (`values("date__month").annotate(Sum)`),
  sin iterar meses en Python.

### Riesgo aceptado
Si el usuario quiere comparar con el año anterior, este gráfico no lo permite.
Queda como mejora futura en una sección de Reportes dedicada.

---

## D-007 - Eliminacion completa del modulo de Presupuestos

**Issue relacionada:** PRD-REMOVE-BUDGETS  
**Fecha:** 2026-03-29  
**Estado:** En ejecucion

### Contexto
El producto incluia un modulo completo de presupuestos mensuales por categoria
(`apps.budgets`) con integracion en dashboard, navegacion lateral, perfil de usuario
y suite de tests. Se decidio remover la funcionalidad por completo.

### Decision
Eliminar el bloque de Presupuestos de manera total, incluyendo:
- app Django `apps.budgets`
- rutas, vistas, formularios, admin y templates del modulo
- integracion en dashboard y navegacion
- referencias de perfil ligadas a alertas de presupuesto
- fixtures, tests, documentacion y roadmap asociados

### Justificacion
- El modulo no es estructural para el registro de gastos, ingresos, ahorro o categorias.
- No existen otros modelos que dependan de `Budget` mediante claves foraneas entrantes.
- El mayor acoplamiento es de UI, reportes y tests, lo que permite una remocion controlada
  sin redisenar el dominio principal.

### Ejecucion
El plan operativo detallado, con orden de trabajo y archivos alcanzados, queda documentado en:

`docs/REMOVE_BUDGETS_PLAN.md`

### Estado actual
- la UI ya no expone Presupuestos
- `apps.budgets` ya no forma parte del runtime principal
- fixtures y tests acoplados al modulo fueron retirados o reescritos
- ya existe una migracion transicional para eliminar `budgets_budget`
- la limpieza documental esta en curso
- la remocion de persistencia en base de datos queda como frente pendiente

---

## D-009 — CSP permite unsafe-inline en style-src

**Fecha:** 2026-05-04
**Estado:** ✅ Decisión tomada

### Contexto
El dashboard usa inline styles para valores dinámicos generados en el template
(ancho del progress bar, height del ranking, color dots de categorías).
La CSP sin `'unsafe-inline'` los bloqueaba en ambos entornos, rompiendo
visualmente la barra de progreso y el scroll del ranking.

Se evaluó migrar a `data-*` + JS, pero `element.style.X = ...` desde JavaScript
también es un inline style y queda igualmente bloqueado por CSP.

### Decisión
Agregar `'unsafe-inline'` a `CSP_STYLE_SRC` en dev.py y prod.py.
El color del progress bar se resuelve con clases Bootstrap (`bg-success/warning/danger`)
para no depender de inline color; el resto de los estilos estáticos permanecen inline.

### Justificación
- App personal sin contenido generado por usuarios — el vector de XSS vía CSS
  es teórico y de impacto mínimo.
- La alternativa correcta (CSS custom properties con nonce) requiere integración
  con django-csp nonce y refactor de templates, complejidad desproporcionada
  para el contexto actual.

### Riesgo aceptado
`unsafe-inline` en `style-src` permite inyección de estilos si existiera XSS,
pero no ejecución de scripts. En una app sin UGC el riesgo es aceptable.
