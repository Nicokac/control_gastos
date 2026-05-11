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

## D-004 — healthz con rate limiting en memoria

**Issue relacionada:** H-007  
**Fecha:** 2026-03-08 / Implementado 2026-05-09  
**Estado:** ✅ Implementado

### Contexto
`/healthz/` es una ruta pública que ejecuta una query a la DB en cada request.
Sin rate limiting podría usarse para amplificar carga sobre la DB.

### Decisión
Throttle simple en memoria en `config/urls.py`: máximo 10 requests por IP en ventana de 60 segundos. Retorna HTTP 429 si se supera el límite.

### Justificación
- Sin dependencias extra (usa `defaultdict` + `time.monotonic()`).
- Render Free ya aplica rate limiting externo; esto es una segunda capa liviana.
- `django-axes` está orientado a login, no a endpoints públicos.
- El health checker de Render (`User-Agent: Render/1.0`) queda excluido del throttle — llama cada 5 segundos y un 429 hace que Render mate el proceso.

### Riesgo aceptado
El dict en memoria se resetea con cada restart del proceso (Render Free reinicia frecuentemente). No persiste entre workers si se escala horizontalmente — aceptable para el contexto actual.

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

---

## D-010 — Feedback via Gmail SMTP, sin app ni modelo propio

**Fecha:** 2026-05-04
**Estado:** ✅ Implementado

### Contexto
Se necesitaba un formulario de feedback (bugs, mejoras, preguntas) accesible desde
el sidebar que enviara un email al administrador con los datos del reporte.

### Decisión
Implementar como vista en `apps.core` (`FeedbackView`) sin modelo de base de datos.
El reporte se envía directamente por email usando `send_mail()` de Django con el
backend SMTP ya configurado en `email_backend.py`.

### Justificación
- La infraestructura SMTP ya existía (`apply_email_settings`, `EMAIL_HOST`, etc.).
- No se necesita persistencia: el email es suficiente como destino del reporte.
- Agregar un modelo requeriría migraciones y gestión en el admin sin valor adicional.
- En dev, el backend de consola imprime el email en el terminal sin configuración extra.

### Variables de entorno requeridas (prod)
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — credenciales Gmail SMTP
- `FEEDBACK_EMAIL` — destinatario (default: `kachuknm@gmail.com`)

### Riesgo aceptado
Sin persistencia, los reportes solo existen en la bandeja de entrada del admin.
Si el email falla silenciosamente en producción, el reporte se pierde.
Mitigación: `fail_silently=False` + logging del error + mensaje de error al usuario.

---

## D-011 — Jerarquía de categorías: grupo → subcategoría (FK self)

**Fecha:** 2026-05-07
**Estado:** ✅ Implementado (Fases 1–5)

### Contexto
Las categorías pasaron de ser una lista plana a una jerarquía de dos niveles:
**grupos** (agrupadores visuales, sin parent) → **subcategorías** (las que se asignan
a cada gasto/ingreso, con parent apuntando a un grupo).

### Decisión
Implementar con FK self en `Category.parent = ForeignKey("self", null=True, blank=True)`.
Se decidió limitar a dos niveles (no árbol arbitrario) para simplificar las queries,
los selectores de formulario y la lógica de dashboard.

### Fases implementadas

1. **Modelo**: FK self + `is_subcategory` property + `get_categories_by_group()` + migraciones
2. **Formularios de gastos/ingresos**: selector agrupado con radio buttons bajo cabeceras de grupo
3. **Dashboard**: donut y ranking agrupados por grupo padre (con fallback a subcategoría si no tiene parent)
4. **Filtro de lista de gastos**: filtra por `category__parent_id` (grupo), no por subcategoría
5. **Edición de categorías**: campo `parent` visible al editar subcategorías para mover entre grupos; `?parent=<pk>` en CREATE pre-selecciona el grupo

### Por qué dos niveles

- Los gastos del mundo real se entienden por grupos ("Comida", "Transporte"), no por subcategorías granulares ("Supermercado", "Colectivo").
- Dos niveles cubren el 100% de los casos de uso sin la complejidad de `django-mptt` o `treebeard`.
- `get_categories_by_group()` hace una sola query con `select_related("parent")` — sin N+1.

### Riesgo aceptado (D-011)

Si en el futuro se necesita más de un nivel de jerarquía, la estructura actual de `parent`
solo admite un nivel. Mitigación: la FK self podría extenderse, pero requeriría refactor
de las queries de dashboard y de los selectores.

---

## D-012 — timezone.localdate() en lugar de timezone.now().date()

**Fecha:** 2026-05-08
**Estado:** ✅ Corregido

### Contexto
La app mostraba el día siguiente a partir de las 21:00 hora Argentina. El código usaba
`timezone.now().date()` que devuelve la fecha en UTC. Argentina es UTC-3, por lo que
a las 21:00 local ya son las 00:00 UTC del día siguiente.

### Decisión
Usar `timezone.localdate()` en todo el código de producción que determina "hoy":
vistas, formularios, utils y modelos. `timezone.localdate()` aplica el `TIME_ZONE`
configurado (`America/Argentina/Buenos_Aires`) antes de extraer la fecha.

### Archivos corregidos
- `apps/core/utils.py` — `get_current_month_year()`, `get_years_choices()`
- `apps/expenses/views.py`, `apps/income/views.py`, `apps/reports/views.py`
- `apps/expenses/forms.py`, `apps/income/forms.py`
- `apps/savings/forms.py` — validación de fecha futura
- `apps/savings/models.py` — property `is_overdue`

### Por qué no se tocaron los tests
Los tests usan `timezone.now().date()` para construir datos de prueba (fechas de gastos).
Eso está bien: en el entorno de test la zona horaria no afecta la lógica que se verifica,
y cambiarlos a `localdate()` no aportaría cobertura adicional.

---

## D-013 — Feedback: API HTTP de Resend en lugar de SMTP

**Fecha:** 2026-05-09
**Estado:** ✅ Resuelto

### Contexto
El formulario de feedback (`/feedback/`) fallaba en producción porque Render Free tier
bloquea conexiones salientes en puertos SMTP (25, 465, 587). Se intentaron Gmail SMTP
y Resend SMTP — ambos bloqueados.

### Decisión
Usar la API HTTP de Resend (`resend.Emails.send()`) en lugar del backend SMTP de Django.
La API opera sobre HTTPS (puerto 443), compatible con Render Free.

### Implementación
- `FeedbackView.form_valid()` en `apps/core/views.py` usa `resend.Emails.send()` directamente.
- `RESEND_API_KEY` se lee desde variable de entorno via `settings.RESEND_API_KEY`.
- `DEFAULT_FROM_EMAIL=onboarding@resend.dev` (dominio de prueba de Resend; sin dominio verificado solo se puede enviar al email de la cuenta).
- `FEEDBACK_EMAIL` y `ADMIN_EMAIL` deben coincidir con el email registrado en Resend mientras no se verifique un dominio propio.

### Riesgo aceptado
Sin dominio verificado en Resend, el `from` queda como `onboarding@resend.dev` y el destinatario debe ser el mismo email de la cuenta. Para enviar a cualquier destinatario con remitente propio, verificar un dominio en resend.com/domains.

---

## D-014 — Deudas técnicas

**Fecha:** 2026-05-09 / Actualizado 2026-05-10

### DT-001 — Resend sin dominio verificado

**Estado:** ⏳ Pendiente (configuración externa)

Sin dominio propio verificado en Resend, el remitente queda fijado en `onboarding@resend.dev` y el destinatario debe coincidir con el email de la cuenta Resend. Para desbloquear envío a cualquier destinatario con remitente propio, verificar un dominio en resend.com/domains y actualizar `DEFAULT_FROM_EMAIL`. No requiere cambios en código.

### DT-002 — Selector de año en gráfico de evolución mensual

**Estado:** ✅ Resuelto (v0.16.0)

El gráfico de evolución ahora incluye un selector de año en el encabezado del card. Al seleccionar un año anterior se muestran los 12 meses completos; para el año actual se muestra enero hasta el mes en curso. Los años disponibles se calculan dinámicamente desde el primer año con datos del usuario.

### DT-003 — healthz: throttle migrado a Django cache

**Estado:** ✅ Resuelto (v0.16.0)

El rate limiting de `/healthz/` se migró de un `dict` en memoria a `django.core.cache`. Con `LocMemCache` (actual) el comportamiento es equivalente pero thread-safe. Para escalar a múltiples workers solo se necesita cambiar `CACHES.BACKEND` a Redis — sin cambios en la lógica del endpoint.

### DT-004 — Tests de integración para mensajes toast en CRUD

**Estado:** ✅ Resuelto (v0.17.0)

Los mensajes toast del framework `django.contrib.messages` generados en operaciones CRUD (crear, editar, eliminar) ahora están cubiertos por tests de integración en todos los módulos:

- **Expenses**: `TestExpenseCreateMessages`, `TestExpenseUpdateMessages`, `TestExpenseDeleteMessages`
- **Income**: `test_create_income_success_adds_success_message`, `test_update_income_adds_success_message`, `test_delete_income_adds_success_message` (corregido: ahora aserta el contenido del mensaje)
- **Categories**: `TestCategoryToastMessages` (Create, Update, Delete)
- **Savings**: `TestSavingToastMessages` (Create, Update, Delete); movimientos ya cubiertos previamente

Los tests usan `follow=True` + `response.context["messages"]` para verificar el mensaje exacto, no solo el status code.

### DT-005 — Sidebar: inconsistencia de comportamiento en mobile

**Estado:** ✅ Resuelto (v0.18.0)

Dos correcciones:
1. **JS — `initMobileOffcanvas()`**: al hacer click en un link dentro del offcanvas mobile, se cierra automáticamente antes de navegar (evitaba que quedara abierto tras cambio de página). Al cruzar el breakpoint md (rotación), se llama `bsOffcanvas.hide()` para limpiar el estado del offcanvas.
2. **CSS**: se agregó una media query `(min-width: 768px)` que oculta el backdrop y el offcanvas mobile cuando el viewport es desktop, previniendo que un backdrop residual bloquee la interfaz tras rotar de portrait a landscape.

### DT-006 — Categorías: orden solo alfabético, sin reordenamiento manual

**Estado:** ✅ Resuelto (v0.21.0)

Las categorías se ordenan alfabéticamente. No hay UI de reordenamiento manual (drag-and-drop o flechas). Evaluar si es necesario según feedback de usuarios.

El problema de scroll en listas largas se resolvió con grupos colapsables (v0.20.0): cada grupo puede expandirse/colapsarse y el estado persiste en localStorage.

### DT-007 — Gastos/Ingresos: sin búsqueda por texto

**Estado:** ✅ Resuelto (v0.19.0)

Se agregó campo `q` en `BaseFilterForm` (heredado por `ExpenseFilterForm` e `IncomeFilterForm`). Los views aplican `description__icontains=q` cuando el parámetro está presente. El campo aparece como primer elemento del formulario de filtros en ambos listados. La búsqueda es case-insensitive y se puede combinar con los demás filtros (mes, año, categoría).

### DT-008 — Exportación de historial (CSV)

**Estado:** ✅ Resuelto (v0.22.0)

Se agregaron `ExpenseExportView` e `IncomeExportView` que heredan de sus respectivas list views para reutilizar la lógica de filtros. La descarga respeta los filtros activos y genera un CSV con BOM (compatible con Excel). Filename con formato `gastos DD.MM.YYYY.csv` / `ingresos DD.MM.YYYY.csv`.

### DT-009 — Dashboard: widget de Gastos Fijos

**Estado:** ⏳ Pendiente

El dashboard no muestra el estado de los gastos fijos del mes. Agregar un widget que muestre "X de Y pagados este mes" con link a `/recurring/`, similar al resumen que ya existe en la lista de gastos fijos.

### DT-010 — Gastos Fijos: tooltips con Bootstrap en íconos de estado

**Estado:** ✅ Resuelto (v0.23.0)

Los íconos de estado usan `data-bs-toggle="tooltip"` + `data-bs-title` en lugar de `title` nativo. `initTooltips()` ya existía en `main.js` y se inicializa en `DOMContentLoaded`.
