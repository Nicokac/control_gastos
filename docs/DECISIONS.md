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

**Nota (2026-06-14):** `expense_type` fue eliminado por completo del modelo, no solo reubicado. Ver commit `b57d2b7`.

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

**Estado:** ✅ Resuelto (v0.23.0)

Widget agregado entre los KPI cards y la distribución de gastos. Muestra pagados/total con barra de progreso y badge de vencidos. Color del card según estado del mes. Solo visible si el usuario tiene gastos fijos activos.

### DT-010 — Gastos Fijos: tooltips con Bootstrap en íconos de estado

**Estado:** ✅ Resuelto (v0.23.0)

Los íconos de estado usan `data-bs-toggle="tooltip"` + `data-bs-title` en lugar de `title` nativo. `initTooltips()` ya existía en `main.js` y se inicializa en `DOMContentLoaded`.

### DT-011 — Ingresos recurrentes

**Estado:** ✅ Resuelto (v1.4.8)

Nuevo módulo `apps/recurring_income` con modelo `RecurringIncome` (nombre, categoría, día esperado de cobro, notas, activo). CRUD completo, lista con toggle de inactivos, estado por mes (cobrado/pendiente/vencido). Botón "Registrar cobro" pre-completa el formulario de Ingreso con categoría y descripción. El cobro queda vinculado via FK `Income.recurring`. Sección "Ingresos Fijos" en sidebar bajo PLANIFICACIÓN. Ver DT-047 para widget pendiente en dashboard.

### DT-012 — Reportes anuales

**Estado:** ✅ Resuelto (v1.7.0)

Vista de reporte anual con comparativa mes a mes: gastos, ingresos, ahorro y balance para cada mes del año. Exportable a xlsx. Complementa el gráfico de evolución mensual del dashboard con una tabla detallada y selector de año. Adicionalmente se agregó exportación xlsx del resumen mensual desde el dashboard.

### DT-013 — Emails transaccionales síncronos en request path

**Estado:** ⏳ Pendiente

`_send_verification_email`, `_send_welcome_email` y `FeedbackView` hacen llamadas HTTP a Brevo de forma síncrona durante el ciclo de request/response. Si Brevo tarda o falla, el usuario espera hasta el timeout (10s). La solución correcta es una cola de tareas (Celery + Redis, o Django-Q). No se implementa ahora porque Render Free no incluye workers adicionales sin costo extra. Aceptable en MVP con bajo volumen de registros.

### DT-014 — `alert_threshold` en User sin funcionalidad activa

**Estado:** ✅ Resuelto (v1.4.9)

Campo `alert_threshold` expuesto en `ProfileForm` y en el template de perfil bajo "Preferencias", junto a moneda principal. En el dashboard, cuando `expense_percentage >= alert_threshold`, aparece una alerta amarilla/roja con link "Cambiar umbral". La barra de progreso cambia a `bg-danger` al superar el umbral y vuelve a `bg-success` cuando está por debajo. El umbral se pasa al contexto del dashboard desde `DashboardView.get_context_data()`.

### DT-015 — Ingresos recurrentes

**Estado:** ✅ Resuelto (v1.4.8) — ver DT-011.

---

### DT-016 — Nombres duplicados entre categorías Sistema y usuario

**Estado:** ✅ Resuelto (v1.1.1)

`CategoryForm.clean_name()` ya validaba duplicados del usuario pero no contra categorías de Sistema. Se corrigieron dos bugs relacionados: (1) `category_type` se resolvía antes de que el campo `type` pasara por `cleaned_data`, dejando la query con tipo vacío; (2) `model.clean()` lanzaba `ValidationError({"user": ...})` pero el form no tiene ese campo, causando `ValueError` en `_post_clean`. Ambos corregidos en `forms.py`. Cobertura agregada en `TestCategoryFormDuplicates`.

### DT-017 — Búsqueda y filtro en Categorías

**Estado:** ✅ Resuelto (v1.3.1)

Campo de búsqueda independiente dentro de cada card (Gastos / Ingresos). Filtra grupos y subcategorías por nombre en tiempo real vía `category_list.js` (compatible con CSP). Incluye botón `×` para limpiar. Los grupos con coincidencia se expanden automáticamente.

### DT-018 — Layout de dos columnas en Categorías con scroll asimétrico

**Estado:** ✅ Resuelto (v1.3.1)

La columna de Gastos suele ser más larga que la de Ingresos. El layout side-by-side hace que al scrollear, la columna de Ingresos quede huérfana arriba. En móvil/pantallas cortas esto desorienta. Opciones: layout de una sola columna con secciones separadas, o scroll independiente por columna. Requiere rediseño del layout.

### DT-019 — Mensajes de error de validación inconsistentes entre formularios

**Estado:** ✅ Resuelto (v1.2.2)

Los formularios de depósito y movimiento de ahorro usaban mensajes genéricos o exponían errores técnicos del form. Estandarizados al patrón `"No pudimos registrar X. Revisá los campos marcados."` que usa el resto de la app.

### DT-020 — Campo "Cotización del dólar" sin valor sugerido al seleccionar USD

**Estado:** ✅ Resuelto (v1.4.9)

Opción B implementada: el `get_initial()` de `ExpenseCreateView` e `IncomeCreateView` busca el último gasto/ingreso en USD del usuario y usa su `exchange_rate` como valor inicial. El campo renderiza el valor en el atributo HTML `value`. En `transaction_form.js`, `toggleExchangeRate()` lee `exchangeRateInput.defaultValue` al habilitar el campo USD y lo copia a `value` si no hay valor actual. El fix es puramente client-side; el backend ya enviaba el dato correctamente.

---

## D-016 — Enhancements relevados por QA — Dashboard

### DT-021 — Dashboard: selector de período (mes/año)

**Estado:** ✅ Resuelto (v1.2.2)

Flechas `‹` `›` en el header del dashboard. La vista lee `?month=X&year=Y` y pasa el período a todos los métodos de datos (balance, recurring, distribución). La flecha derecha y botón "Hoy" solo aparecen fuera del mes actual. No se permite navegar al futuro. El selector de año del gráfico preserva el mes seleccionado vía hidden input.

### DT-022 — Dashboard: cards de Gastos e Ingresos no navegan al detalle

**Estado:** ✅ Resuelto (v1.2.2)

Cards envueltos en `<a>` apuntando a `/expenses/?month=X&year=Y` e `/income/?month=X&year=Y`. Se agregó clase `card-hover` con efecto de elevación al pasar el mouse.

### DT-023 — Dashboard: ranking de categorías sin drill-down

**Estado:** ✅ Resuelto (v1.2.2)

Se agrega `pk` al dict de grupos y subcategorías en `_get_expense_distribution`. El nombre del grupo linkea a `/expenses/?month=X&year=Y&category=<pk>` y cada subcategoría a `/expenses/?month=X&year=Y&subcategory=<pk>`.

### DT-024 — Dashboard: card de Ingresos sin variación vs. mes anterior

**Estado:** ✅ Resuelto (v1.2.2)

El card de Gastos muestra variación porcentual vs. el mes anterior. El card de Ingresos mostraba texto estático "Ingresos estables" sin comparativa cuantitativa. La lógica de variación ya estaba implementada para Gastos. Se aplicó la misma lógica al card de Ingresos: muestra badge verde/rojo con porcentaje, "Sin variación vs [mes]" si es exactamente 0%, o nada si no hay datos del mes anterior.

### DT-025 — Dashboard: ausencia de widget de ahorro y metas

**Estado:** ✅ Resuelto (v1.2.2)

Card de Ahorro integrada en la fila de KPIs junto a Gastos e Ingresos (layout 3 columnas). Muestra total acumulado, barra de progreso global y cantidad de metas activas. Siempre visible — muestra "Sin metas activas" cuando no hay ninguna.

### DT-026 — Dashboard: gráfico de evolución mensual no configurable

**Estado:** ✅ Resuelto (v1.4.2)

Los puntos del gráfico de evolución son clickeables y navegan al dashboard de ese mes (`?month=M&year=Y`). El cursor cambia a pointer al hacer hover. El tooltip incluye el texto "Click para ver ese mes". El selector de año ya existía; el cambio de rango por meses (3/6/12) queda como mejora futura de baja prioridad.

### DT-027 — Dashboard: ausencia de widget de gastos fijos pendientes

**Estado:** ✅ Resuelto (v1.2.2)

El widget de Gastos Fijos ya existía con resumen numérico. Se extendió para mostrar los badges de cada gasto pendiente con nombre y día de vencimiento. Los vencidos se muestran en rojo, los pendientes en gris. La lógica de estado se calcula en la view y se pasa como `recurring_pending`.

### DT-028 — Dashboard: barra de progreso sin contexto temporal

**Estado:** ✅ Resuelto (v1.2.2)

La barra de balance muestra "Gastaste el X% de tus ingresos" sin indicar en qué día del mes estamos. Resuelto agregando "Día 21 de 31" junto al balance disponible, usando `today.day` y el filtro `|date:"t"` de Django.

---

## D-017 — Enhancements relevados por QA — Gastos

### DT-029 — Mes financiero personalizado por fecha de cobro

**Estado:** ✅ Resuelto (v1.5.0)

Campo `financial_month_start_day` (1-28, default 1) en el modelo `User`, expuesto en `ProfileForm` y en el template de perfil. Nueva función `get_financial_period(month, year, start_day)` en `core/utils.py` que calcula el rango [start_day del mes, start_day del mes siguiente). El dashboard usa ese rango para calcular gastos, ingresos y balance. El texto "Día X de Y" refleja los días transcurridos dentro del período financiero y muestra "(período financiero)" cuando el inicio es distinto a 1. El texto es clickeable y navega a Mi Perfil.

### DT-030 — Gastos: búsqueda dentro del picker de categorías

**Estado:** ✅ Resuelto (v1.4.1)

Input de búsqueda encima del grid de categorías en los formularios de Gasto e Ingreso. Filtra en tiempo real ocultando los botones que no coinciden y colapsa el grupo entero si no queda ninguna subcategoría visible. Incluye botón `×` para limpiar. Lógica en `initCategorySearch()` dentro de `transaction_form.js`, compatible con CSP.

### DT-030 — Gastos: duplicar un gasto existente

**Estado:** ✅ Resuelto (v1.2.2)

Botón "Duplicar" en cada fila de la lista que abre el formulario con `?duplicate=<pk>`. El `get_initial` del `ExpenseCreateView` detecta el parámetro y precarga categoría, descripción, monto, moneda, cotización, método de pago y tipo.

### DT-031 — Gastos: estado vacío no distingue filtros activos vs. mes sin datos

**Estado:** ✅ Resuelto (v1.2.2)

Se agrega `has_active_filters` al contexto (detecta q, category, subcategory, payment_method, expense_type). El template muestra "No hay gastos que coincidan con los filtros aplicados." con botón "Limpiar filtros" cuando hay filtros activos, y el mensaje original con "Registrar primer gasto" cuando el mes genuinamente no tiene datos.

### DT-032 — Gastos: búsqueda de texto no opera sobre nombre de categoría

**Estado:** ✅ Resuelto (v1.2.2)

El filtro `q` usa un `Q` combinado que opera sobre `description`, `category__name` y `category__parent__name`. El mismo patrón se aplicó a Ingresos en la misma versión.

### DT-033 — Gastos: campos "Método de pago" y "Tipo" ocultos bajo "Opciones avanzadas"

**Estado:** ✅ Resuelto (v1.2.2)

Eliminado el collapse "Más filtros". Los campos de método de pago y tipo se movieron como columnas inline dentro de la fila de filtros del formulario de lista.

### DT-034 — Gastos: eliminación requiere navegar a página separada

**Estado:** ✅ Resuelto (v1.2.2)

Modal Bootstrap reutilizable con un único form cuyo `action` se actualiza via `data-delete-url` al abrir. La lógica JS vive en `expense_list.js` (externo, compatible con CSP). El mismo patrón se aplicó a Ingresos en v1.2.2 (ver DT-039).

### DT-035 — Gastos: ordenamiento por columnas

**Estado:** ✅ Resuelto (v1.4.1)

Headers Fecha, Categoría, Descripción y Monto son clickeables en las listas de gastos e ingresos. Parámetros `?order_by=<campo>&dir=<asc|desc>`. El header activo muestra un chevron indicando dirección. Clic repetido invierte el orden. Implementado via template tag `sort_url` en `currency_filters.py` que construye la URL preservando los filtros activos.

### DT-036 — Gastos: paginación sin salto directo a página

**Estado:** ✅ Resuelto (v1.4.4)

Input numérico + botón en el componente `pagination.html` para saltar directamente a cualquier página. Solo visible cuando hay más de 2 páginas. Preserva todos los filtros activos via hidden inputs. Prev/next ahora también muestran estado disabled en los extremos.

### DT-037 — Gastos: panel "Ver resumen" sin desglose por categoría individual

**Estado:** ✅ Resuelto (v1.4.3)

El panel "Ver resumen" ahora incluye tres columnas: Por categoría (ordenado por monto descendente, con nombre del grupo padre), Por tipo de gasto y Por método de pago. La query agrega por `category_id` sobre el queryset ya filtrado, sin query adicional al servidor.

### DT-038 — Gastos: filtro por rango de monto

**Estado:** ✅ Resuelto (v1.4.3)

Campos "Monto mínimo" y "Monto máximo" en la fila de filtros de la lista de gastos. Filtran sobre `amount_ars`. Se incluyen en la detección de filtros activos para el estado vacío diferenciado.

### DT-039 — Gastos/Ingresos: paridad de funcionalidad entre secciones

**Estado:** ✅ Resuelto (v1.2.2)

Ingresos recibió: duplicar con `?duplicate=<pk>`, modal de eliminación con confirmación (`income_list.js`), búsqueda por categoría/grupo (Q filter), `has_active_filters` con estado vacío diferenciado, fecha en `d/m/Y`, grupo visible sobre el badge y `select_related("category__parent")`.

### DT-040 — Gastos: donut chart de distribución por categoría

**Estado:** ✅ Resuelto (v1.4.5)

Donut chart (Chart.js) en el panel "Ver resumen" agrupando por grupo de primer nivel (no subcategoría). El hueco central muestra "Total" y el monto; en hover muestra el nombre y monto del grupo activo. Segmentos < 3% se fusionan en "Otros" (gris). Colores sincronizados con los chips de categoría. Click en una porción filtra la tabla al grupo vía `?category=<pk>`. Inicialización lazy al abrir el collapse. Tipo de gasto y método de pago incluyen porcentaje y barra de progreso.

### DT-041 — Gastos: barras horizontales de ranking por categoría

**Estado:** ✅ Resuelto (v1.4.5)

Integrado en la leyenda del donut como barra de 4px debajo de cada ítem. Cada fila muestra: dot de color, nombre del grupo, porcentaje y monto. La barra usa `background-color` inline para evitar conflictos con Bootstrap. La card es scrolleable con fade inferior que desaparece al llegar al fondo. Click en cualquier fila filtra la tabla al grupo.

### DT-042 — Gastos: línea de acumulado diario dentro del mes

**Estado:** ✅ Resuelto (v1.4.6) — extendido en v1.5.1

Gráfico de línea (Chart.js) con el gasto acumulado día a día, visible en "Ver resumen" cuando hay un mes específico filtrado (o el mes actual por default). Se oculta cuando el filtro es solo por año. Query agrupada por `date` sobre el queryset ya filtrado. Tooltip muestra "Día X · $ monto". Inicialización lazy junto al donut al abrir el collapse. En v1.5.1 se agregó un gráfico de barras paralelo ("Gastos por día") que muestra el gasto individual de cada día — click en una barra filtra la tabla a `?date_from=&date_to=` de ese día exacto. Ambos gráficos conviven en layout de dos columnas.

### DT-043 — Gastos: barras apiladas de evolución mensual

**Estado:** ✅ Resuelto (v1.4.6)

Gráfico de barras apiladas (Chart.js) visible en "Ver resumen" cuando el filtro tiene año sin mes específico. Muestra los 12 meses en el eje X con los top 6 grupos apilados; grupos restantes se agrupan en "Otros". Eje Y con formato abreviado (k/M). Tooltip muestra grupo y monto, omite series con $0. Mutuamente excluyente con el acumulado diario (DT-042).

### DT-047 — Dashboard: widget de Ingresos Fijos pendientes

**Estado:** ✅ Resuelto (v1.4.8)

Widget de Ingresos Fijos en el dashboard, idéntico en estructura al de Gastos Fijos. Muestra cobrados/total con barra de progreso verde y badges amarillos para los pendientes. Solo visible cuando el usuario tiene al menos un ingreso fijo activo. Implementado via `_get_recurring_income_data()` en `DashboardView`.

### DT-046 — Landing: demo visual con screenshots reales de la app

**Estado:** ✅ Resuelto (v1.5.2)

La landing actual (`templates/core/landing.html`) tiene solo texto e íconos — sin ninguna visualización real de la app. Se decidió agregar screenshots reales integradas en un layout estilo "feature showcase" (imagen + texto alternados). No se eligió demo en vivo (Opción C) por riesgo de corrupción de datos sin workers disponibles en Render Free.

**Pantallas a capturar** (con datos de ejemplo del usuario Nicolas en dev):

| Pantalla | Qué mostrar |
|---|---|
| Dashboard | Balance, barra de progreso, KPIs, donut de distribución, widget de gastos fijos |
| Gastos | Lista con "Ver resumen" abierto mostrando el donut y acumulado diario |
| Ingresos | Lista del mes con dos registros |
| Metas de ahorro | Meta "Vacaciones 2026" con barra de progreso al 24% |
| Gastos Fijos | Lista con estados pagado/pendiente/vencido |

**Datos de ejemplo cargados en dev (usuario Nicolas):**

Gastos Mayo 2026:
- Supermercado Coto $28.500 · Alimentación · Débito · Variable
- Delivery Pedidos Ya $4.200 · Alimentación · Crédito · Variable
- Carnicería $12.000 · Alimentación · Efectivo · Variable
- Verdulería $3.800 · Alimentación · Efectivo · Variable
- SUBE $5.000 · Transporte · Débito · Fijo
- Uber/Cabify $8.600 · Transporte · Crédito · Variable
- Nafta $22.000 · Transporte · Efectivo · Variable
- Luz (Edesur) $18.500 · Hogar · Débito · Fijo
- Gas $9.200 · Hogar · Débito · Fijo
- Expensas $45.000 · Hogar · Transferencia · Fijo
- Farmacia $6.800 · Salud · Crédito · Variable
- Médico clínico $15.000 · Salud · Efectivo · Variable
- Obra social $28.000 · Salud · Débito · Fijo
- Netflix $8.500 · Streaming · Crédito · Fijo
- Spotify $4.200 · Entretenimiento · Crédito · Fijo
- Cine $7.500 · Entretenimiento · Efectivo · Variable
- Librería $5.600 · Educación · Efectivo · Variable
- Ropa $35.000 · Varios · Crédito · Variable
- Regalo cumpleaños $12.000 · Varios · Efectivo · Variable
- Restaurante $18.900 · Alimentación · Crédito · Variable

Ingresos Mayo 2026:
- Sueldo Mayo $500.000 · Sueldos
- Ingreso Proyecto $85.000 · Freelance

Gastos Fijos:
- Internet Fibertel $12.500 · vence día 5 · Pagado
- Gimnasio $18.000 · vence día 10 · Pendiente
- Netflix $8.500 · vence día 15 · Pendiente

Meta de ahorro:
- Vacaciones 2026 · Objetivo $500.000 · Ahorrado $120.000 (24%)

**Implementación:** las imágenes van en `static/img/landing/`. El layout alterna imagen (derecha/izquierda) con texto descriptivo por sección.

### DT-044 — Gastos Fijos: soporte para gastos temporales (cuotas)

**Estado:** ✅ Resuelto (v1.4.7)

Campos opcionales `total_installments` y `start_date` en `RecurringExpense`. Propiedades `installments_paid`, `installments_remaining` y `auto_deactivate_if_complete()`. Al registrar el último pago, el gasto se desactiva automáticamente. Badge en la lista: "6 cuotas" sin pagos, "cuota 3/6" con pagos. Validación cruzada en el formulario: ambos campos son requeridos juntos o ninguno.

### DT-045 — Gastos Fijos: lista sin filtro de inactivos

**Estado:** ✅ Resuelto (v1.4.7)

Inactivos ocultos por defecto. Cuando existen, aparece el botón "Mostrar inactivos (N)" en el header de la tabla. Al activarlo muestra todos y el botón cambia a "Ocultar inactivos (N)". Toggle via query param `?inactive=1`.

### DT-048 — Ícono representativo de la app

**Estado:** ✅ Resuelto (v1.12.0)

La app web usa el ícono genérico de Bootstrap Icons (`bi-wallet2`) y no tiene favicon personalizado. La app mobile usa `Icons.account_balance_wallet` de Material Design en la pantalla de login. Ninguna de las dos tiene un ícono propio que identifique la marca.

**Why:** se detectó al desarrollar la app mobile que la identidad visual carece de un ícono propio. El ícono del sistema es funcional pero no diferencia la app.

**Resolución:** se diseñó un ícono personalizado (billetera azul con íconos de casa, personas, dinero y tendencia alcista). Se configuró `flutter_launcher_icons` en `pubspec.yaml` y se generaron todos los tamaños para Android (mdpi→xxxhdpi + adaptive icon API 26+) e iOS. Ícono fuente en `assets/icons/app_icon.png`.

### DT-049 — Mobile: deshacer "marcar pagado" en gastos fijos

**Estado:** ✅ Resuelto (v1.12.0)

Al marcar un gasto fijo como pagado desde la app mobile, se crea un `Expense` vinculado al recurrente. No existe forma de revertir esta acción desde la app — el usuario debe ir a la lista de Gastos y eliminar el registro manualmente.

**Why:** acción detectada durante el desarrollo de `recurring_list_screen.dart`. No hay endpoint `unmark-paid` en la API.

**Resolución:** se agregó `POST /api/v1/recurring/{id}/unmark-paid/` en `RecurringExpenseViewSet`. Elimina el `Expense` del mes actual vinculado al recurrente y reactiva el recurrente si se había desactivado por completar la última cuota. La opción "Revertir pago" aparece en el menú contextual de la app mobile solo cuando el estado es `paid`.

### DT-050 — Integración Cafecito (donaciones)

**Estado:** ✅ Resuelto (v1.13.0)

La app no tiene ningún mecanismo para que los usuarios apoyen económicamente el proyecto. Cafecito.app es la plataforma de donaciones más usada en Argentina y es apropiada como primer paso antes de implementar un modelo de suscripción completo.

**Why:** se quiere validar la disposición a pagar de los usuarios antes de invertir en la infraestructura de pagos recurrentes (Stripe + modelo freemium). Cafecito es cero fricción técnica y permite recibir apoyo voluntario de forma inmediata.

**Resolución:** botón "Invitame un Cafecito" agregado en el sidebar web (pie), en la tarjeta "Acerca de" del perfil web, y en la pantalla "Acerca de" de la app móvil. URL: [cafecito.app/niicok](https://cafecito.app/niicok)

### DT-052 — Cotización del dólar automática

**Estado:** ✅ Resuelto (v1.14.0)

Al seleccionar USD en gastos o ingresos, la cotización oficial se completa automáticamente vía dolarapi.com (precio de venta). Se cachea 15 minutos en Django cache. El usuario puede editarlo libremente. Al editar un registro existente, se muestra el valor guardado originalmente como referencia. No se implementó modelo `ExchangeRate` — la caché por request es suficiente para el volumen actual.

---

### DT-053 — Detección de suscripciones encubiertas

**Estado:** ⏳ Pendiente

Si un gasto con la misma descripción y monto similar aparece 2-3 meses consecutivos, la app no lo detecta ni sugiere convertirlo en gasto fijo.

**Why:** muchos gastos recurrentes (Spotify, Netflix, membresías) se cargan manualmente mes a mes sin que el usuario los vincule. Ya existe toda la infraestructura de `recurring`; solo falta la detección.

**Camino de resolución:** query mensual sobre `Expense` agrupada por descripción normalizada. Si aparece ≥3 meses seguidos con monto en rango ±20%, mostrar banner en la lista de gastos: "¿Convertir en gasto fijo?". Un click pre-completa el formulario de `RecurringExpense`.

---

### DT-054 — Proyección de cierre de mes

**Estado:** ✅ Resuelto (v1.15.0 web · v1.16.0 mobile)

El dashboard muestra el gasto acumulado hasta hoy pero no proyecta cómo cerrará el mes al ritmo actual.

**Why:** los datos pasados informan; la proyección permite actuar. "A este ritmo terminás el mes con −$45.000" convierte la app de registro histórico en herramienta de decisión.

**Resolución web (v1.15.0):** con el período financiero ya configurable (`financial_month_start_day`), calcular `gasto_diario_promedio * días_restantes` y sumarlo al acumulado. Mostrar como badge en el hero del dashboard. Sin modelo nuevo, solo lógica en `DashboardView`.

**Resolución mobile (v1.16.0):** los campos `projection_available`, `projected_expense` y `projected_balance` se agregaron al endpoint `GET /api/v1/dashboard/`. La lógica reutiliza `get_financial_period()` con el `financial_month_start_day` del usuario, idéntica a la web. En Flutter, `_ProjectionBanner` se muestra entre `BalanceCard` y los botones rápidos solo cuando `projection_available == true`.

---

### DT-055 — Importación de resúmenes bancarios

**Estado:** 🧪 Resuelto en beta (v1.20.1) — Fases 1 y 2

La carga era 100% manual. No existía forma de importar movimientos desde el banco.

**Why:** la fricción de carga manual es la principal causa de abandono en apps de finanzas personales. Importar el resumen del banco y mapear columnas automáticamente es el salto de calidad más grande posible en UX.

**Resolución (Fase 1 — beta):** vista de importación (`/expenses/import/`) que acepta PDF de resumen Visa Macro. `apps/expenses/importers.py` parsea con `pdfplumber` usando coordenadas de columna (robusto a descripciones de largo variable). Preview editable con Tom Select, contador de filas categorizadas, botón de confirmación bloqueado hasta completar categorías. Impuestos (sellos, IIBB, IVA, DB.RG) se agrupan en una sola fila "Impuestos tarjeta", deschequeada por defecto. Sugerencia de categoría por historial del usuario (descripción exacta) con prioridad sobre sugerencia por nombre. Modal para crear subcategoría — y grupo nuevo si hace falta — sin salir de la pantalla. Filas en USD piden la cotización del día (precompletada desde `dolarapi.com`) antes de habilitar la confirmación. Detección de duplicados contra gastos ya cargados (fecha+descripción+monto), marcados visualmente y excluidos por defecto. Errores de fila al confirmar muestran detalle (cuál fila y por qué). Progreso de categorización se guarda en `localStorage` atado a un hash del resumen, para no perderlo ante un cierre accidental de pestaña — requiere volver a subir el mismo PDF para restaurarlo, ya que el archivo no se persiste en el servidor.

**Resolución (Fase 2 — beta, alcance completo):** cada fila del preview tiene un selector de tipo (Puntual / Fijo / Cuota), con sugerencia automática — `installment_match` detecta el patrón "Cuota X/Y" en la descripción, y una lista curada de comercios conocidos (`_KNOWN_FIXED_SERVICES` en `importers.py`) sugiere "Fijo". El usuario siempre confirma manualmente el tipo, la sugerencia nunca se aplica sola. Al confirmar una fila Fijo/Cuota, `ExpenseImportConfirmView` busca un `RecurringExpense` activo del usuario con nombre exactamente igual a la descripción: si existe, vincula el `Expense` nuevo a ese recurrente sin crear uno duplicado (esto absorbe el alcance que originalmente iba a ser la Fase 3); si no existe, crea el `RecurringExpense` — con `total_installments`, `starting_installment` y `start_date` tomados de la fila para las cuotas — y vincula el gasto. Las cuotas sin ambos números completos (por si el parser falló) bloquean la confirmación con mensaje de error específico. `_build_import_preview` expone `matches_existing_recurring` por fila (match exacto contra recurrentes activos del usuario); en el preview aparece "Se vincula a tu gasto fijo existente" apenas el usuario marca esa fila como Fijo/Cuota, antes de confirmar — evita que el vínculo sea una sorpresa recién visible después de importar.

**Por qué sigue en beta:** soporte actual limitado a resúmenes Visa Banco Macro — el agregado de otros bancos queda como roadmap futuro (nuevo parser por banco, o generalizar `importers.py` para detectar el formato). La lista de servicios conocidos para sugerir "Fijo" es curada a mano y no cubre todos los casos; el usuario puede corregir el tipo manualmente en cualquier fila. El badge "Beta" se mantiene visible en el botón "Importar" de la lista de gastos y en el header de la pantalla de importación — ambos aclaran el alcance actual (Banco Macro) — hasta validar el flujo completo con más resúmenes reales y, eventualmente, sumar más bancos.

**Riesgo aceptado:** un resumen de otro banco no va a parsear correctamente (el parser está atado a las coordenadas X específicas del layout de Macro). Si el usuario sube un PDF de otro formato, el resultado es una lista vacía o filas mal separadas, sin error explícito más allá de "no se encontraron transacciones". El matching de recurrentes existentes es por nombre exacto — si el usuario edita la descripción de una fila antes de confirmar, no va a coincidir con un recurrente ya creado y se genera uno nuevo en su lugar.

**Paridad con mobile — decisión consciente de no portar (2026-09-29):** DT-055 completo (Fases 1 y 2) es **web-only**. No hay equivalente en Flutter ni está planeado en el corto plazo.

**Why:** el flujo requiere subir un archivo, revisar un preview con muchas filas editables (categoría, tipo, cuotas), crear categorías al vuelo y resolver casos borde (USD, duplicados, impuestos agrupados) — una experiencia que encaja mejor en pantalla grande que en mobile. Además la funcionalidad todavía está en beta y atada a un solo banco; portarla ahora significaría mantener dos implementaciones de algo que puede seguir cambiando de forma.

**Estado de paridad general (relevado 2026-09-29):** mobile 1.16.0 está sincronizado con la web hasta v1.18.0 inclusive (DT-063 — semáforo de gastos fijos — ya portado, ver `PendingRecurringCard`). La única brecha actual entre mobile y web es DT-055 (v1.19.0 en adelante), y es intencional.

**Cuándo reevaluar:** cuando DT-055 salga de beta (parser probado con más resúmenes reales, o soporte multi-banco), evaluar un flujo simplificado en mobile — sin las interacciones ricas de la web, priorizando algo directo (subir PDF, ver preview, confirmar) sobre paridad exacta con la UI web.

---

### DT-056 — Insights automáticos mensuales

**Estado:** ⏳ Pendiente

La app muestra datos pero no genera observaciones sobre ellos.

**Why:** "gastaste 23% más en Delivery que tu promedio de 6 meses" o "mejor mes de ahorro del año" son frases que generan engagement y valor percibido sin que el usuario tenga que interpretar los gráficos.

**Camino de resolución:** conjunto de reglas sobre queries que ya existen (evolución mensual, distribución por categoría). Renderizar como tarjetas en el dashboard o en una sección "Resumen del mes". Sin ML, solo comparativas sobre datos históricos del usuario.

---

### DT-057 — Calendario de compromisos futuros

**Estado:** ✅ Resuelto (v1.17.0 web · v1.16.0 mobile)

Ya se soportan gastos en cuotas y gastos fijos, pero no había vista prospectiva de los próximos meses.

**Why:** saber cuánto del ingreso futuro ya está comprometido en cuotas y vencimientos permite planificar antes de asumir nuevos compromisos.

**Resolución:** se descartó el timeline de 3-6 meses y el formato calendario — el usuario quería un número directo, no un calendario visual. Se implementó `get_next_month_commitment()` en `apps/core/utils.py`, reutilizado por la vista web (`DashboardView`) y la API (`/api/v1/dashboard/`). Suma `last_expense.amount_ars` de los `RecurringExpense` activos (incluye cuotas en curso, ya excluidas si se completaron por `auto_deactivate_if_complete`) y lo compara contra `last_income.amount_ars` de los `RecurringIncome` activos. Los recurrentes sin pago/cobro previo no tienen monto estimable y se listan aparte (`*_unestimated`) para no subestimar el total con $0. Solo se calcula para el período actual — no aplica al navegar meses pasados. Widget nuevo en dashboard web y mobile (`_NextMonthCommitmentCard`).

---

### DT-058 — Patrimonio neto (cuentas y saldos)

**Estado:** ⏳ Pendiente

La app trackea flujo (gastos e ingresos) pero no el saldo real de cada cuenta del usuario.

**Why:** sin modelo de cuentas, la app no puede responder "¿cuánto tengo en total?". Efectivo, banco, billetera virtual y dólares físicos son realidades cotidianas en Argentina.

**Camino de resolución:** modelo `Account` (nombre, tipo, moneda, saldo inicial). Los gastos e ingresos pueden vincularse opcionalmente a una cuenta para actualizar el saldo. Widget de patrimonio neto en el dashboard. Transformaría la app de tracker de flujo a foto financiera completa.

---

### DT-059 — Gastos compartidos v2: balances y liquidación

**Estado:** ⏳ Pendiente

Hoy `SharedExpense` registra quién pagó pero no calcula quién le debe a quién ni permite liquidar saldos.

**Why:** el paso natural después de registrar gastos compartidos es saber el balance neto entre los miembros del hogar (estilo Splitwise). Es la funcionalidad que hace que otros usuarios de la casa también quieran usar la app.

**Camino de resolución:** calcular balance neto por par de miembros sobre el período seleccionado. Vista de liquidación: "Juan le debe $12.300 a Ana". Botón "Liquidar" que registra un pago de compensación. En el futuro: invitar a otro usuario real de la app al hogar (requiere modelo de invitaciones).

---

### DT-060 — Modo oscuro en la web

**Estado:** ✅ Resuelto (v1.15.0)

La app web no tiene modo oscuro. Bootstrap 5.3 ya trae soporte nativo via `data-bs-theme="dark"`.

**Why:** detectado en auditoría UX (−5 puntos). Es una preferencia de una parte significativa de los usuarios y Bootstrap 5.3 lo hace relativamente directo.

**Camino de resolución:** toggle en el perfil/settings que persiste en `localStorage`. Aplicar `data-bs-theme` al `<html>`. Revisar los estilos custom en `main.css` que puedan necesitar ajustes para el tema oscuro (principalmente colores hardcodeados).

---

### DT-061 — Ahorro por reglas automáticas

**Estado:** ⏳ Pendiente

Las metas de ahorro requieren depósito manual. No hay forma de automatizar aportes periódicos.

**Why:** "depositar automáticamente 10% de cada ingreso en la meta Vacaciones" reduce la fricción de ahorro y mejora el cumplimiento de metas. La vinculación gasto→meta ya existe; falta automatizarla.

**Camino de resolución:** modelo `SavingRule` (porcentaje o monto fijo, trigger: al registrar ingreso / mensual, meta destino). Al cumplirse el trigger, crear automáticamente un `SavingMovement`. UI simple en la pantalla de detalle de la meta.

---

### DT-062 — Export/backup completo de datos del usuario

**Estado:** ⏳ Pendiente

La exportación actual cubre solo gastos e ingresos en Excel con filtros. No hay forma de exportar todos los datos ni de importarlos de vuelta.

**Why:** "mis datos son míos" es un argumento de confianza que reduce la fricción de registro. Complementa el delete de cuenta que ya existe. También sirve como mecanismo de migración si el usuario cambia de dispositivo.

**Camino de resolución:** vista de exportación completa que genera un ZIP con JSONs de todas las entidades del usuario (gastos, ingresos, categorías, metas, gastos fijos, compartidos). Opcionalmente, importación desde ese mismo formato para restore o migración.

---

### DT-051 — Modelo de suscripción freemium

**Estado:** ⏳ Pendiente

La app no tiene diferenciación entre usuarios gratuitos y de pago. Todo el contenido es accesible para todos los usuarios registrados. No hay modelo de ingresos recurrentes implementado.

**Why:** el proyecto apunta a generar ingresos pasivos como SaaS. El modelo freemium está definido en `docs/MONETIZACION.md` pero no está implementado técnicamente.

**Camino de resolución (ver MONETIZACION.md para detalle completo):**
1. Fase M-1: definir features Free vs Premium, diseñar modales de upgrade, registrar cuenta Stripe
2. Fase M-2: modelo `Subscription` en Django + integración Stripe + guards en API
3. Fase M-3: página de precios y billing en web
4. Fase M-4: paywall en Flutter + RevenueCat
5. Fase M-5: trial 14 días + lanzamiento

---

### DT-063 — Urgencia en gastos fijos pendientes (días restantes y semáforo)

**Estado:** ✅ Resuelto (v1.18.0 web · v1.16.0 mobile)

Hoy el card "Gastos Fijos" del dashboard (web y mobile) lista los ítems pendientes de forma plana, sin jerarquía de urgencia. El modelo `RecurringExpense` ya tiene `due_day` y `status_for()` que distingue `pending`/`overdue`, pero esa información no se traduce en ninguna señal visual de proximidad.

**Problema concreto:** un gasto que vence mañana y uno que vence en 20 días se muestran igual. No hay alerta si algo vence sin registrar pago.

**Why:** el objetivo es que el usuario sepa de un vistazo qué pagar hoy, qué mañana y qué puede esperar, sin tener que ir a la sección de Gastos Fijos para entenderlo.

**Resolución:** se agregó `days_until_due` en la API y en la view del dashboard (solo para el período actual). Los chips de gastos fijos pendientes se ordenan por proximidad y muestran "Vencido" / "Hoy" / "Mañana" / "En X días" / "día N" con semáforo de color rojo/ámbar/gris. Sin migraciones ni cambios de modelo. Corregidos también dos tests preexistentes frágiles por fecha fija.

**Ver también:** DT-057 (comprometido del mes que viene, ya resuelto).

---

### DT-064 — Tests de expenses/income con fecha UTC en vez de localdate

**Estado:** 🟡 Parcialmente resuelto

`conftest.py` (`expense_factory`, `income_factory`) y varios tests en `apps/expenses/tests/test_views.py` usaban `timezone.now().date()` para fechar gastos/ingresos de prueba. Como `timezone.now()` devuelve UTC y Argentina es UTC-3, cualquier test corrido entre las 21:00 y las 23:59 hora local construye una fecha que ya es "mañana" en UTC — un día que puede caer fuera del mes actual real si se corre cerca de fin de mes, haciendo fallar los tests que dependen del filtro de "mes actual" de `ExpenseListView` (`timezone.localdate()`).

**Why:** detectado al correr la suite completa de noche — 4 tests de `TestExpenseListView`/`TestExpenseExportView` fallaron porque el gasto de prueba quedaba fechado en el mes siguiente. Mismo patrón que ya se había corregido puntualmente en DT-063 ("dos tests preexistentes frágiles por fecha fija") y en D-012 para el código de producción, pero sin aplicarlo a los fixtures compartidos.

**Resolución aplicada:** `expense_factory` e `income_factory` en `conftest.py` ahora usan `timezone.localdate()` como default. Los 2 call-sites de `test_views.py` que fallaron (`test_list_shows_total_period_summary`, `test_list_builds_payment_method_summary`) se corrigieron puntualmente.

**Pendiente:** quedan ~20 ocurrencias más de `timezone.now().date()` en `apps/expenses/tests/test_views.py` (la mayoría usa la fecha como valor arbitrario dentro del mismo test, sin depender de un filtro de mes — bajo riesgo real, pero mismo antipatrón). No se tocaron todas para no hacer un refactor grande fuera del alcance de la tarea que detectó el bug. Si vuelve a aparecer un fallo nocturno similar, candidato a limpiar todas de una vez.

---

### DT-065 — Botón "ojo" para ocultar montos sensibles

**Estado:** ✅ Resuelto (v1.21.0 web · Mobile 1.16.0+9)

No existía forma de ocultar rápidamente los montos en pantalla (balance, gastos, ingresos) en web ni mobile. Si alguien usa la app en público (transporte, oficina compartida), sus datos financieros quedaban expuestos a cualquiera que mire la pantalla.

**Why:** patrón estándar en apps de finanzas personales y bancos — un ícono de ojo que alterna entre mostrar el valor real y un placeholder, sin ocultar la navegación ni el resto de la UI.

**Alcance resuelto:** solo Dashboard (balance principal, KPIs, proyección, comprometido del mes que viene, donut de distribución, últimos movimientos, gastos fijos pendientes). Persistente por dispositivo — no requiere backend ni sincroniza entre dispositivos.

**Resolución (web):** nuevo filtro de template `sensitive_currency` (`apps/core/templatetags/currency_filters.py`) que envuelve el monto en `<span class="sensitive-amount">`, usado solo en `dashboard.html` (no toca el filtro `currency` original usado en el resto de la app). CSS en `main.css` (`body.amounts-hidden .sensitive-amount { filter: blur(6px) }`), compatible con modo oscuro. JS en `dashboard.js` con persistencia en `localStorage`.

**Resolución (mobile):** `amounts_visibility_provider.dart` (`Notifier<bool>` con `shared_preferences`, mismo patrón que `theme_provider.dart`) + widget `SensitiveText` que reemplaza `Text` en los montos del dashboard, mostrando `••••••` cuando está oculto.

---

### DT-066 — Fecha de vencimiento de gasto fijo: no editable

**Estado:** 🚫 Descartado — error de reporte, confirmado por el usuario

Se había reportado que no se podía editar el día de vencimiento (`due_day`) de un gasto fijo después de creado. Revisando el código (`apps/recurring/forms.py`, `apps/api/v1/serializers/recurring.py`, `mobile/lib/features/recurring/screens/recurring_form_screen.dart`) el campo nunca estuvo bloqueado — ni en `read_only_fields` ni deshabilitado en ningún formulario. El usuario confirmó que el campo funciona correctamente y que el reporte había sido un error propio (probablemente una confusión puntual al usar la app). No se tocó código.

---

### DT-067 — Balance positivo de fin de mes no se traslada automáticamente

**Estado:** ⏳ Pendiente (a definir enfoque)

Al cerrar un mes, el balance positivo (ingresos − gastos) no se traslada como "sobrante" al mes siguiente ni se vincula a ninguna meta de ahorro. El usuario tiene que registrarlo manualmente como un ingreso o un depósito a una meta.

**Why:** es un paso manual repetitivo y fácil de olvidar — el dato (cuánto sobró) ya existe en el dashboard, solo falta un mecanismo para "hacer algo" con él automáticamente.

**Opciones a evaluar (a decidir antes de implementar):**
1. **Sugerencia pasiva**: al cierre de mes, el dashboard muestra un banner "Te sobraron $X este mes — ¿querés destinarlo a una meta de ahorro?" con un botón que pre-completa un `SavingMovement`. Cero automatismo, el usuario sigue confirmando cada vez.
2. **Regla automática configurable**: el usuario define una vez "el sobrante de cada mes va a la meta Vacaciones" y el sistema lo aplica solo al cierre de cada período financiero (se conecta con DT-061, ahorro por reglas automáticas, que ya cubre un mecanismo similar para % de ingresos).
3. **Categoría especial "Ahorro del mes"**: un `Expense` o `SavingMovement` especial que se genera automáticamente con el sobrante, sin pedir confirmación — más automático pero más arriesgado si el cálculo de "sobrante" no es exacto (gastos pendientes de registrar, por ejemplo).

**Riesgo a resolver en cualquier opción:** definir qué es "balance positivo" con precisión — ¿ingresos menos gastos del período financiero completo? ¿se espera a que termine el mes o se puede anticipar? ¿qué pasa si el usuario carga gastos de ese mes después de haber trasladado el sobrante?

---

### DT-068 — Pop-up de aviso de nuevas actualizaciones

**Estado:** ✅ Resuelto (v1.22.0 web · Mobile 1.16.0+10)

No había ningún aviso dentro de la app cuando salía una versión nueva. El usuario se enteraba solo si entraba a "Novedades" por su cuenta, o si la Play Store actualizaba la app mobile sin que lo note.

**Why:** mejora la percepción de que el producto está vivo y evita que el usuario mobile quede en una versión vieja sin saberlo, sobre todo mientras el proyecto está en fase de iteración rápida.

**Hallazgo durante la implementación:** ya existía un sistema de detección "hay novedades" en web vía `localStorage` (`whats_new_seen`), usado para mostrar un badge "Nuevo" en el link del sidebar, marcado como visto al entrar a `/novedades/`. El plan original de este DT proponía un campo en la DB (`User.last_seen_version`) — se descartó por ser redundante: se optó por reusar la misma clave de `localStorage` ya existente, una sola fuente de verdad en vez de dos sistemas de tracking en paralelo.

**Resolución (web):** `apps/core/context_processors.py` expone `LATEST_RELEASE` (la primera entrada de `WHATS_NEW`) a todos los templates. `base.html` renderiza un modal Bootstrap con el contenido de la última versión si el usuario está logueado. `main.js` (`initWhatsNewModal()`) decide si mostrarlo comparando `localStorage.whats_new_seen` contra la versión del modal — si coincide, no se muestra. Al cerrar el modal (cualquier botón) o hacer clic en "Ver todas las novedades", se marca como visto con la misma clave que ya usaba el badge del sidebar.

**Resolución (mobile):** no existe pantalla de "Novedades" en mobile, así que se implementó un `AlertDialog` nativo (`core/utils/whats_new.dart`) que se dispara una vez al entrar al dashboard, comparando `ApiConstants.appVersion` contra `shared_preferences` (misma key `whats_new_seen_version`). El resumen de texto (`ApiConstants.latestReleaseSummary`) es manual — hay que actualizarlo junto con `appVersion` en cada bump, igual que ya se hacía con la versión.

**Riesgo aceptado:** en mobile, el resumen de novedades es un string fijo (no una lista completa como en web) porque no existe una estructura tipo `WHATS_NEW` en el cliente Flutter — mantenerla sincronizada manualmente es la misma carga operativa que ya existía para `appVersion`, no se agrega proceso nuevo.

---

### DT-069 — Color del botón "Invitame un Cafecito" inconsistente en mobile

**Estado:** ✅ Resuelto (Mobile 1.16.0+10)

El botón de Cafecito en mobile no mantenía el mismo color que en la web.

**Why:** es parte de la identidad de marca del botón (DT-050); debería verse igual en ambas plataformas.

**Causa real:** no era un problema de tema claro/oscuro como se sospechaba — el color estaba directamente hardcodeado mal: `Color(0xFFFF5C00)` (naranja) en vez de `#7C64BF` (violeta de marca). La pantalla "Acerca de" (`about_screen.dart`) nunca tuvo el color correcto desde que se implementó.

**Resolución:** corregido a `Color(0xFF7C64BF)`, y se fijó explícitamente `color: Colors.white` en el ícono y el texto del botón para que no hereden del tema del dispositivo (mismo criterio que el botón web, que tampoco depende de `data-bs-theme`).

---

### DT-070 — Evaluación e instalación de skills de agente (Claude Code)

**Estado:** 🟡 En progreso — fase 1 (instalación oficial) ✅ y fase 2 (skill custom `sync-docs`) ✅ completadas 2026-10-03

Se evaluó qué skills/plugins de Claude Code podrían asistir el desarrollo del proyecto, organizados en 4 módulos: (1) publicación en tiendas, (2) deuda técnica/roadmap/versionado, (3) diseño visual/UX, (4) QA/testing. Se pidieron dos análisis externos independientes y se cruzaron.

**Why:** el proyecto es mantenido por un único desarrollador con asistencia de Claude Code. Automatizar partes repetitivas del proceso (checklist de Play Store, sincronización de docs, QA) reduce la carga manual y el riesgo de olvidos (ya pasó con `FLUTTER_ROADMAP.md` desactualizado 3 meses — ver más abajo).

**Hallazgo clave — Módulo 2 no tiene cobertura pública:** ninguna skill encontrada en ninguno de los dos análisis maneja el patrón específico de este repo — `docs/DECISIONS.md` con formato `DT-XXX`, `docs/FLUTTER_ROADMAP.md`, y doble versionado desacoplado (`APP_VERSION` en `apps/core/views.py` para web, `version` en `mobile/pubspec.yaml` para mobile, cada uno con su propio changelog). Las alternativas más cercanas (`changelog-generator`, `doc-freshness`, `docs-sync`) asumen un esquema de versión única con Conventional Commits, que no calza con este proyecto. **Decisión: construir una skill propia con `skill-creator` en vez de adaptar una de terceros.**

**Instaladas (alta confianza — oficiales), confirmado 2026-10-03:**
- `dart-flutter@dart-flutter` v1.0.6 (scope user) — plugin oficial de Flutter/Dart (`flutter/agent-plugins`), base de conocimiento mobile
- `superpowers@claude-plugins-official` v6.4.1 (scope user) — ya estaba instalado de antes; metodología de trabajo (brainstorm → plan → TDD → debug → verify), capa de proceso, no de dominio
- `code-review@claude-plugins-official` y `frontend-design@claude-plugins-official` — ya estaban instalados de antes (no forman parte de esta evaluación, pre-existentes)
- Skills oficiales de Anthropic (`skill-creator`, `webapp-testing`) — ya disponibles sin instalación adicional en esta sesión

**Nota (resuelta):** `claude plugin list` mostró `superpowers@claude-plugins-official` aparentemente duplicado — v5.1.0 en scope `local` y v6.4.1 en scope `user`. Investigado: la instalación `local` v5.1.0 pertenece a otro proyecto (`portafolio_de_activos`, instalada 2026-06-16), no a `control_gastos` — cada proyecto tiene su propio scope `local` independiente. No afecta a este repo, que usa la v6.4.1 de scope `user`. No se tocó.

**Instalado — `flutter@flutter-skills` v1.0.0 (scope user), confirmado 2026-10-03:**
Marketplace `zakariaf/Flutter-Skills` (40 skills para Riverpod 3.x + Material 3 + go_router — prácticamente el stack mobile real de este proyecto). Se reconsideró la decisión original de descartarlo (ver "Descartadas" más abajo, ahora corregida): el README del repo aclara que las 40 skills fueron destiladas de +10 apps Flutter en producción, reconciliadas a **un solo stack canónico** (misma terminología, mismo vocabulario, sin contradicciones entre sí) y revisadas adversarialmente — no es un paquete sin curar de un autor individual, el riesgo que motivó el descarte original no aplica acá. Instalado completo en vez de una sola skill porque el propio repo lo ofrece así vía plugin marketplace (mismo mecanismo que `dart-flutter`), y las 40 ya vienen reconciliadas entre sí.

Relevantes para el Módulo 3 (diseño/UX) de esta evaluación:
- `ui-states-and-feedback` — resuelve loading/empty/error/content en un solo switch, ataca directo las preguntas de UX ad-hoc mencionadas al abrir este DT ("¿dónde pongo este botón?", "¿cómo muestro un estado vacío?")
- `design-system-structure` — organización tokens→theme→componentes, con gate CI contra valores sin tokenizar (relevante tras el bug de color hardcodeado de DT-069)
- `accessibility-as-code`, `adaptive-layout`, `testing-strategy`, `release-and-store-shipping` — cobertura adicional útil, no evaluadas a fondo todavía

**Sigue pendiente — el problema de paridad web↔mobile no lo resuelve ninguna skill externa.** Ninguna de las 40 conoce el lenguaje visual específico de este proyecto (qué es "Primary", "Income", "Expense" en este repo puntual) ni compara Bootstrap (web) contra Dart (mobile) — es exactamente el mismo tipo de gap que llevó a construir `sync-docs` para el Módulo 2. Candidata futura: una skill de proyecto `control-gastos-design-system` que defina los tokens reales (colores de Primary/Success/Warning/Danger/Income/Expense/Savings, spacing, radios, etc.) e inspeccione `static/css/` + `templates/` contra `mobile/lib/` para marcar colores hardcodeados y mismatches entre plataformas.

**Evaluadas, pendientes de decisión (requieren probar antes de confiar):**
- Django: tres paquetes comunitarios candidatos (`affaan-m`, `andreassendev`, `jeffallan`) ofrecen `django-patterns`/`django-security`/`django-verification` — elegir uno solo, no mezclar autores
- Play Store compliance: `android/skills` → `play-policy-insights` (oficial Google) cruza código vs. declaraciones de Data Safety, pero está pensado para Android nativo — no confirmado que funcione bien sobre un proyecto Flutter
- UX/accesibilidad adicional: `design-review` (`humbleteam/design-review`, heurísticas de Nielsen + WCAG 2.2, formato Before/After/Why) y una skill de WCAG 2.2 AA dedicada — candidatas para auditar pantallas web existentes, no instaladas todavía

**Descartadas explícitamente:**
- Paquetes grandes de un solo autor sin revisar (40+ skills de `flutter-claude-skills`, distinto del marketplace `zakariaf/Flutter-Skills` ya instalado) — riesgo de instrucciones superpuestas/contradictorias sin curación
- Cualquier skill que requiera credenciales de Google Cloud/Play Console (`yasserstudio/gpc-skills`, `PollyGlot/google-play-cli-skills`) — demasiado sensible sin auditar el código fuente primero
- `git-workflow-automation` / `changelog-generator` — asumen Conventional Commits + versión única, no el esquema real del repo

**Skill custom construida — `sync-docs` (Módulo 2), confirmado 2026-10-03:**
Creada en `.claude/skills/sync-docs/` (skill de proyecto, no global) con `skill-creator`. Automatiza el Paso 2-5 del flujo manual que se venía siguiendo toda esta sesión: entrada en `docs/DECISIONS.md` (`DT-XXX` o la sub-serie `DTD-XXX` para descartes dentro de `D-015`), entrada en `CHANGELOG.md`, propuesta de bump de versión (web/mobile, **nunca aplicado sin confirmación explícita del usuario**), y actualización de `docs/FLUTTER_ROADMAP.md` cuando el cambio toca mobile. Se dispara explícitamente (el usuario la pide), no automáticamente.

Validada con 3 test cases representativos (fix mobile puro, feature web+mobile, reporte investigado y descartado), corridos con y sin la skill (subagentes en paralelo) en 2 iteraciones:

- **Hallazgo principal (ambas iteraciones):** sin la skill, el bump de versión se aplica directamente sin pedir confirmación en el 100% de los casos que lo involucran — exactamente el riesgo que la skill fue diseñada para evitar. Con la skill, 0% de los casos aplicó un bump sin proponerlo primero.
- **Iteración 1 → 2:** pass rate con skill pasó de 94% a 100% tras dos ajustes — (a) agregar un ejemplo explícito y literal de qué fix NO amerita una entrada en `DECISIONS.md` (el criterio "decisión de diseño no-obvia" por sí solo no bastaba, tanto el agente con skill como el baseline crearon una entrada de más para un fix simple en la primera corrida); (b) documentar explícitamente la sub-serie `DTD-XXX` que ya existía en el repo real pero no estaba mencionada en el draft inicial de la skill.
- Resultados completos (incluyendo HTML de revisión lado a lado) en `sync-docs-workspace/` — directorio local, no versionado (agregado a `.gitignore`).

**Próximo paso:** evaluar una por una las candidatas de Django y Play Store antes de confiarles tareas reales (quedan pendientes, no se avanzó en esta sesión).

---

### DT-071 — Mobile: colores semánticos hardcodeados en vez de tema

**Estado:** ✅ Resuelto

Revisión de las 18 pantallas de la app mobile con las skills `design-system-structure`, `ui-states-and-feedback`, `adaptive-layout` y `accessibility-as-code` (plugin `flutter@flutter-skills`, ver DT-070). Hallazgo de mayor repetición: `app.dart` define `ColorScheme.fromSeed(seedColor: Color(0xFF0d6efd))`, pero casi ninguna pantalla lo consume. En su lugar, cada archivo repetía literales hex para la temática de cada tipo de dato: `Colors.red[700]`/`Colors.red.withValues(alpha: 0.05)` (gastos), `Colors.green[700]` (ingresos), `Colors.orange[700]` (pendientes/vencidos), `Color(0xFF0d6efd)` (compartidos), `Color(0xFF28a745)` (ahorros). Confirmado en 21 archivos (14 pantallas + 7 widgets compartidos).

**Why:** mismo patrón de bug que causó DT-069 (color de marca hardcodeado mal en `about_screen.dart`) — sin una fuente única de verdad, cada pantalla puede divergir del resto o de la web sin que se note hasta que alguien lo reporta.

**Resolución:** se creó `mobile/lib/core/theme/app_semantic_colors.dart`, un `ThemeExtension<AppSemanticColors>` registrado en `_lightTheme`/`_darkTheme` de `app.dart`, con slots separados por tipo de uso (decisión tomada explícitamente para no mezclar significados que hoy comparten el mismo hex por casualidad):

- **Tipo de dato:** `expense`, `income`, `savings`, `shared`, `recurring`
- **Resultado de una acción:** `success`, `danger` (snackbars de éxito/error genéricos, antes mezclados con los colores de ingreso/gasto)
- **Urgencia de vencimiento:** `overdue`, `dueSoon`, `onTrack` (antes mezclados con los mismos verdes/rojos/naranjas)

Los valores usan la paleta real del proyecto (`#dc3545`, `#28a745`, `#fd7e14`, `#0d6efd` — `CATEGORY_COLOR_CHOICES`) en vez de los `Colors.red[700]`/`Colors.green[700]` de Material que se usaban antes, lo que de paso corrige pequeñas diferencias de tono contra la web. Se migraron las 21 pantallas/widgets detectadas, accediendo a los colores vía `context.semanticColors.<slot>` (extensión `AppSemanticColorsX` sobre `BuildContext`). Dos casos sin slot exacto (depósito/retiro en `saving_detail_screen.dart`, pago/reversión en `recurring_list_screen.dart`) se resolvieron reusando `success`/`dueSoon` en vez de crear slots de un solo uso.

Se actualizaron `balance_card_test.dart` y `pending_recurring_card_test.dart` (fallaban porque el `MaterialApp` de prueba no registraba la extensión) agregando `theme: ThemeData(extensions: const [AppSemanticColors.light])`. Verificado con `flutter analyze` (sin issues nuevos) y `flutter test` (mismo resultado que el baseline: 40 pasan / 12 fallan por un problema de aislamiento entre archivos de test preexistente, no relacionado a este cambio — pendiente de investigar aparte).

Los colores de "gasto"/"ingreso" en textos de error/advertencia puntuales (ej. el aviso de "este grupo no tiene subcategorías" en los formularios) se dejaron mapeados al slot de tipo de dato correspondiente por consistencia visual del formulario, no porque sean semánticamente un error.

---

### DT-072 — Mobile: errores de red mostrados sin mapear (`e.toString()` crudo)

**Estado:** ✅ Resuelto

Mismo origen que DT-071 (revisión con las 4 skills de `flutter@flutter-skills`). Segundo hallazgo de mayor repetición: cuando un `AsyncValue`/`FutureBuilder` cae en estado de error, la pantalla renderiza el mensaje de la excepción directo (`Text('Error: $e')` o equivalente) en vez de un mensaje mapeado y amigable. Confirmado en 13 de las 18 pantallas (`categories_screen`, `expense_form_screen`, `expense_list_screen`, `income_form_screen`, `income_list_screen`, `recurring_form_screen`, `recurring_list_screen`, `saving_detail_screen`, `savings_list_screen`, `settings_screen`, `shared_expense_form_screen`, `shared_expense_list_screen`, `household_members_screen`). Además, varios de estos casos (`expense_form_screen`, `income_form_screen`, `recurring_form_screen`, `shared_expense_form_screen`, `settings_screen`) no ofrecían ninguna acción de reintento junto al error (incluyendo el selector "¿Quién pagó?" en `shared_expense_form_screen`, que silenciaba el error por completo con `SizedBox.shrink()`).

**Why:** el texto de una excepción (`SocketException`, `DioException`, etc.) es ruido técnico en inglés que no le dice nada al usuario final sobre qué pasó ni qué puede hacer — y si el texto de la excepción cambia (ej. al actualizar una librería), cambia la UX sin que nadie lo note.

**Resolución:** se creó `mobile/lib/core/widgets/error_state_view.dart`, un `ErrorStateView(error, onRetry, message, compact)` (mismo criterio visual que el `EmptyState` ya existente en `core/widgets/`) que muestra un mensaje genérico amigable con botón de reintento, revelando el detalle técnico de la excepción solo bajo `kDebugMode`. Se agregó un modo `compact` (ícono chico, fila horizontal) para los casos embebidos dentro de un formulario en vez de ocupar la pantalla completa (ej. error al cargar categorías dentro de `expense_form_screen`), distinto del modo completo usado en las pantallas de lista. Migradas las 13 pantallas detectadas; el reintento invalida el provider correspondiente en cada caso (`ref.invalidate(...)` o el `.reload()` del notifier, según cuál expusiera la pantalla).

Un cuarto caso relacionado pero distinto —`settings_screen.dart` retorna `SizedBox.shrink()` si `user == null` dentro del estado `data` (no es loading, error ni contenido real, sino un cuarto estado silencioso)— quedó fuera de esta resolución: es un caso borde raro (solo ocurre en la ventana entre un logout y la navegación fuera de la pantalla) y no es el patrón de "error sin mapear" que motivó esta DT.

---

### DT-073 — Mobile: loading sin forma del contenido final (spinner centrado en vez de skeleton)

**Estado:** ✅ Resuelto

Tercer hallazgo de mayor repetición de la misma revisión con `flutter@flutter-skills` (ver DT-070/071/072). Regla 7 de `ui-states-and-feedback`: el estado de carga debería anticipar la forma del resultado (un esqueleto con la silueta de la lista/card que va a aparecer), no un spinner centrado que no da ninguna pista de qué se está cargando y provoca un salto de layout brusco cuando llega la data. Solo el dashboard (`DashboardSkeleton`) seguía este patrón; las pantallas de lista (`expense_list_screen`, `income_list_screen`, `recurring_list_screen`, `savings_list_screen`, `shared_expense_list_screen`, `household_members_screen`) usaban `Center(child: CircularProgressIndicator())`.

**Why:** mismo motivo que ya justificó `DashboardSkeleton` en su momento — un esqueleto reduce la sensación de espera y evita el salto de layout, pero solo se había aplicado una vez y no se generalizó al resto de las listas.

**Resolución:** se creó `mobile/lib/core/widgets/list_skeleton.dart` (`ListSkeleton(itemCount, withCard)`), reusando los bloques `SkeletonBox`/`SkeletonLine` ya existentes en `core/widgets/skeleton.dart` (los mismos que usa `DashboardSkeleton`). Dos variantes según la silueta real de cada pantalla: tile simple (ícono circular + 2 líneas + monto) para listas tipo `ListTile` (gastos, ingresos, recurrentes, compartidos, miembros del hogar), y `withCard: true` (card con barra de progreso) para ahorros, que usa `Card` + `LinearProgressIndicator` en vez de `ListTile`. `categories_screen.dart` quedó fuera: su estructura (secciones expandibles de grupos/subcategorías) no coincide con ninguna de las dos siluetas y generalizar ahí requeriría un skeleton dedicado, no una reutilización directa.

---

### DT-074 — Mobile: targets táctiles menores a 44x44px en selectores de color/ícono

**Estado:** ✅ Resuelto

Cuarto hallazgo de la revisión con `flutter@flutter-skills` (ver DT-070/071/072/073), regla 8 de `accessibility-as-code`: todo elemento interactivo debe tener un área táctil mínima de 44x44px, aunque el elemento visual sea más chico. Confirmado en `categories_screen.dart` (círculos de color 32x32 y celdas de ícono con `GestureDetector` colapsado al tamaño visual de 40x40 en vez de ocupar la celda del grid) y `saving_form_screen.dart` (círculos de color 36x36 con `InkWell`).

**Why:** un círculo de 32-36px es un blanco difícil de tocar con precisión, sobre todo para usuarios con poca destreza motriz o pantallas grandes con dedos gruesos — el estándar de 44x44 (Apple HIG / Material) existe justamente para evitar toques fallidos en elementos pequeños agrupados.

**Resolución:** en los 3 selectores de color (`categories_screen` grupo/subcategoría, `saving_form_screen`), se envolvió el círculo visual en un `SizedBox(width: 44, height: 44)` + `Center`, manteniendo el tamaño visual del círculo sin cambios — solo crece el área táctil, no el diseño. En el selector de ícono de `categories_screen` (dentro de un `GridView` de celdas ~48x48), el `GestureDetector` envolvía directamente el `Container` de 40x40 sin `Center`, por lo que colapsaba a ese tamaño en vez de ocupar la celda completa del grid — se agregó `Center` para que el `GestureDetector` se estire a toda la celda disponible. El selector de íconos de `saving_form_screen` (72px de ancho + ícono + texto + padding) ya superaba los 44px de alto real sumando su contenido, no requirió cambios.

---

### DT-075 — Mobile: selectores de color/ícono sin nombre accesible para lectores de pantalla

**Estado:** ✅ Resuelto

Quinto hallazgo de la misma revisión con `flutter@flutter-skills` (ver DT-070 a 074), regla de `accessibility-as-code` de no depender solo de una señal visual: los círculos de color en `categories_screen.dart` y `saving_form_screen.dart` indicaban el color seleccionado solo con un borde + ícono de check, pero el color en sí (rojo, verde, azul, etc.) no tenía ningún texto alternativo — un lector de pantalla anunciaba el elemento como un botón sin nombre. El selector de ícono de categorías (42 opciones tipo `bi-cart`, `bi-piggy-bank`) tenía el mismo problema: ningún nombre descriptivo, solo la clave técnica interna.

**Why:** el estado seleccionado ya cumplía parcialmente la regla de "no depender solo del color" (hay un ícono de check visible), pero identificar *cuál* opción es cada círculo — antes de seleccionarla — solo era posible viéndola. Sin nombre accesible, un usuario de lector de pantalla no puede elegir un color o ícono con intención, solo "el tercer botón" sin saber qué representa.

**Resolución:** se creó `mobile/lib/core/constants/category_colors.dart` con `categoryColorNames` (mapa hex→nombre en español para los 10 colores de `CATEGORY_COLOR_CHOICES`) y `categoryColorName(hex)`, reusado en ambas pantallas via `Semantics(label: ..., button: true, selected: ...)` envolviendo cada círculo. Para el selector de ícono de categorías, se agregó `_categoryIconNames` (42 nombres descriptivos, ej. `bi-cart` → "Carrito de compras") y `categoryIconName(name)` en `core/utils/category_icons.dart`, junto al resto de los mapeos de ese mismo ícono, aplicado igual con `Semantics`. El selector de íconos de `saving_form_screen` (6 opciones) no necesitó cambios: ya muestra el nombre como `Text` visible junto al ícono, que un lector de pantalla ya anuncia por defecto.

---

### DT-076 — Mobile: validación de categoría duplicada (snackbar + inline) y en el campo equivocado

**Estado:** ✅ Resuelto

Sexto hallazgo de la misma revisión con `flutter@flutter-skills` (ver DT-070 a 075), tabla de superficie de `ui-states-and-feedback` (inline es lo recomendado para validación de formulario, no snackbar). Los 4 formularios de transacciones (`expense_form_screen`, `income_form_screen`, `recurring_form_screen`, `shared_expense_form_screen`) mostraban "Seleccioná una categoría" en un `SnackBar` desde `_submit()`, aun cuando ya existía un `FormField<int>` con `errorText` conectado — validación duplicada por dos canales distintos.

Al revisar el código se encontró un segundo bug, más relevante: el `FormField` que validaba `_categoryId == null` estaba conectado al `errorText` del campo **"Grupo de categoría"**, no al campo **"Categoría"** (son dos selectores visuales distintos cuando el grupo tiene subcategorías). Si el usuario elegía bien el grupo pero no la subcategoría, el mensaje de error aparecía bajo "Grupo" — un campo ya correctamente completado — en vez de bajo "Categoría", que es el que realmente faltaba.

**Why:** un snackbar es efímero y puede perderse si el usuario no lo ve a tiempo, mientras que el `errorText` inline queda visible hasta que se corrige — mostrar ambos para el mismo error es ruido, y mostrar el error en el campo equivocado directamente confunde sobre qué hay que corregir.

**Resolución:** en los 4 formularios, el `FormField` de "Grupo de categoría" ahora valida `_groupId == null` (su propio campo). Se envolvió el bloque del selector de "Categoría" (el `InkWell`/`InputDecorator` que antes no tenía validación propia) en un nuevo `FormField<int>` que valida `_categoryId == null` y conecta su `errorText`. Se eliminó el chequeo manual + `SnackBar` redundante en `_submit()` de los 4 formularios, dejando solo `if (_categoryId == null) return;` como guarda silenciosa para el caso en que el grupo no tenga subcategorías (ahí no hay campo de "Categoría" visible al que atribuir el error, porque el grupo mismo se usa como categoría).

---

### DT-077 — Mobile: `settings_screen` mostraba pantalla en blanco ante `user == null`

**Estado:** ✅ Resuelto (sin bump de versión — sin impacto visible real)

Caso borde detectado durante DT-072 pero dejado fuera de esa resolución porque no era el mismo patrón ("error sin mapear"). `settings_screen.dart` retornaba `SizedBox.shrink()` dentro del estado `data` de `authProvider` cuando `user == null` — un cuarto estado no representado explícitamente (ni loading, ni error, ni contenido real).

**Why:** se investigó cuándo ocurre realmente: `authProvider` pasa a `AsyncData(null)` de forma sincrónica en `logout()` (`auth_provider.dart:75`), y el `GoRouter` tiene un `redirect` conectado a ese mismo provider vía `refreshListenable` (`app_router.dart:69-83`) que fuerza la navegación a `/login` en cuanto detecta `isLoggedIn == false`. En la práctica, `user == null` en esta pantalla dura exactamente un frame — la pantalla jamás llega a ser percibida por el usuario antes de que el router la reemplace por `/login`. No es un bug con impacto real, pero `SizedBox.shrink()` seguía siendo un estado silencioso sin justificación explícita en el código.

**Resolución:** cambiado a `Center(child: CircularProgressIndicator())` — mismo widget que el estado `loading`, ya que conceptualmente es "esperando salir de esta pantalla", no contenido vacío. Cambio de una línea, sin bump de versión ni entrada en CHANGELOG por no tener impacto visible observable (criterio de CLAUDE.md para cambios internos).

---

### DT-078 — Mobile: `ApiConstants.appVersion` hardcodeada se desincronizó de `pubspec.yaml`

**Estado:** ✅ Resuelto

Durante el release de hoy (DT-071 a 077, 6 bumps de versión: 1.16.0+10 → 1.16.6+17) se detectó que la pantalla "Acerca de" seguía mostrando "Versión 1.16.0" en un dispositivo real, pese a que `pubspec.yaml` ya estaba en 1.16.6. Causa: `about_screen.dart` no leía la versión real del build — usaba `ApiConstants.appVersion`, una constante de texto en `core/constants/api_constants.dart` que había que actualizar a mano en cada bump, y que quedó desactualizada durante toda la sesión (corregida recién al notarlo, fuera del flujo normal de `sync-docs`). `whats_new.dart` (DT-068) también dependía de la misma constante para comparar contra la versión ya vista.

**Why:** es el mismo patrón de fondo que ya motivó DT-071 (colores hardcodeados) — un valor que debería tener una sola fuente de verdad (`pubspec.yaml`) estaba duplicado manualmente en otro archivo, sin nada que verificara la sincronización. Ninguna de las 4 skills de `flutter@flutter-skills` usadas hoy (`ui-states-and-feedback`, `design-system-structure`, `accessibility-as-code`, `adaptive-layout`) tiene jurisdicción sobre esto: analizan patrones de UI en el código, no el proceso de release ni constantes de versión duplicadas entre archivos sin relación estructural visible. La skill `sync-docs` tampoco lo cubre — su alcance es proponer el bump de versión en `pubspec.yaml`/`CHANGELOG.md`/`FLUTTER_ROADMAP.md`, pero nunca fue diseñada para verificar que *otros* archivos que hardcodean la versión (como este) queden sincronizados.

**Resolución:** se agregó la dependencia `package_info_plus` y se eliminó `ApiConstants.appVersion` por completo. `about_screen.dart` ahora lee `PackageInfo.fromPlatform().version` dentro de un `FutureBuilder` (muestra "Versión…" mientras resuelve). `whats_new.dart` usa la misma lectura async para comparar contra la versión ya vista en `shared_preferences` — el formato del string (`version:` de `pubspec.yaml`, sin el build number) es idéntico al que devolvía la constante manual, así que no dispara el popup de novedades de forma espuria a usuarios que ya lo vieron. La pantalla "Acerca de" ya no puede desincronizarse de lo que realmente está compilado, sin depender de que alguien se acuerde de actualizar una constante en cada bump.

---

### DT-079 — Mobile: 5 mejoras relevadas por el usuario tras uso real de la app

**Estado:** ✅ Resuelto

Lista de puntos relevados directamente por el usuario usando la app en el día a día (no por una skill ni revisión automatizada):

1. **Falta de contenido legal en mobile**: la app no tenía acceso a Términos y condiciones ni Política de privacidad, ya publicados en la web (`/terms/`, `/privacy/`).
2. **Inconsistencia visual en Configuración**: los campos de "Cuenta" y "Preferencias" (Email, Nombre, Apellido, Usuario, Moneda, Día de inicio) usaban `OutlineInputBorder()` sin radio (esquinas casi cuadradas), distinto del look del `SegmentedButton` en "Apariencia".
3. **Fuente grande en los mismos campos**: tamaño default de Material (~16px), percibido como grande para una pantalla de configuración densa.
4. **"Gastos por categoría" sin vista de monto**: el gráfico de torta del dashboard solo mostraba el porcentaje de cada categoría, sin forma de ver el acumulado real en pesos.

**Why:** son ajustes de experiencia real detectados con uso cotidiano, no bugs — la app funcionaba correctamente, pero la consistencia visual entre secciones y la falta de una vista alternativa en el gráfico de gastos eran mejoras pendientes de UX que ningún análisis automatizado (ni las skills de `flutter@flutter-skills`, orientadas a patrones de código, no a preferencias de producto) iba a señalar.

**Resolución:**
- **Legal**: 2 `ListTile` nuevos en `about_screen.dart` ("Términos y condiciones", "Política de privacidad") que abren las páginas ya existentes en la web vía `url_launcher`, reusando el mismo patrón que "Sitio web" — sin duplicar contenido legal en dos lugares.
- **Bordes y fuente**: en `settings_screen.dart` se centralizaron `_inputBorder` (radio 12) y `_inputFontSize` (14) como constantes reusadas en los 6 campos de "Cuenta" y "Preferencias".
- **Toggle %/monto**: nuevo `expenseChartViewProvider` (`core/providers/expense_chart_view_provider.dart`, mismo patrón que `amountsHiddenProvider` de DT-065 — persistido en `shared_preferences`) y un `SegmentedButton` chico junto al título en `expense_chart.dart` que alterna cada fila de categoría entre porcentaje y monto (`SensitiveText`, respetando el botón de ocultar montos existente).

---

## D-015 — Deudas técnicas descartadas

Ítems evaluados y descartados conscientemente. Se registran para evitar re-evaluarlos sin contexto.

### DTD-002 — Consistencia visual de categorías Sistema

**Estado:** 🚫 Descartado

**Motivo:** El comportamiento es correcto y uniforme — cualquier grupo (Sistema o usuario) permite agregar subcategorías propias, y las subcategorías de Sistema no tienen editar/eliminar. La aparente inconsistencia reportada era confusión visual por el estado colapsado/expandido, no un bug real. No requiere cambios.

---

### DTD-003 — Estado expandido de grupos en Categorías

**Estado:** 🚫 Descartado

**Motivo:** El comportamiento actual es correcto: todos los grupos arrancan expandidos en la primera visita y el estado se persiste en `localStorage` por ID de grupo (`category_collapsed_groups`). Si un grupo aparece expandido es porque el usuario nunca lo cerró, no porque haya una lógica inconsistente. Cambiar el default a "colapsado" perjudicaría la primera experiencia obligando al usuario a expandir todo. No requiere cambios.

---

### DTD-001 — Presupuestos por categoría

**Estado:** 🚫 Descartado

**Motivo:** Agrega complejidad de configuración (el usuario debe definir límites por categoría cada mes) sin un beneficio claro dado el flujo actual de la app. Los gastos fijos ya cubren el caso de uso de control de compromisos mensuales. Reevaluar si surge demanda concreta de usuarios.

---

## D-017 — Arquitectura de infraestructura en producción

**Fecha:** 2026-05-13
**Estado:** ✅ Verificado y en producción

### Arquitectura real

| Componente | Proveedor | Detalle |
| ---------- | --------- | ------- |
| **Hosting** | Render Free | `control-gastos-fr8z.onrender.com` |
| **Base de datos** | Render PostgreSQL Free | Host interno `dpg-d5e5c8ili9vc73et5r90-a` |
| **Email transaccional** | Brevo API HTTP | Reset, verificación, bienvenida, feedback |
| **Backups DB** | Cloudflare R2 | Dump diario via GitHub Actions, `pg_dump` |
| **Error tracking** | Sentry | DSN configurado en Render |
| **CI/CD** | GitHub Actions | Push a `main` → deploy automático |

### Decisiones tomadas

- **Brevo en lugar de Resend/SMTP**: Render Free bloquea puertos SMTP (25, 465, 587). Brevo ofrece API HTTP sin restricciones. Resend requería dominio propio verificado. Ver D-013.
- **Render PostgreSQL en lugar de Neon**: DB gestionada por el mismo proveedor de hosting. Sin dependencia externa adicional.
- **Cloudflare R2 para backups**: Render Free no incluye backups automáticos ni acceso externo a la DB. El dump se hace desde GitHub Actions usando `DATABASE_URL` con el external URL de Render. R2 tiene 10 GB free tier.

### Variables de entorno activas (sin secretos)

```env
ALLOWED_HOSTS=control-gastos-fr8z.onrender.com
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=False
ADMIN_EMAIL=kachuk_nm@hotmail.com
FEEDBACK_EMAIL=kachuk_nm@hotmail.com
SERVER_EMAIL=kachuknm@gmail.com
```

Secretos gestionados en Render Dashboard: `SECRET_KEY`, `DB_*`, `BREVO_API_KEY`, `SENTRY_DSN`.

### Variables huérfanas a limpiar

Las siguientes variables están en Render pero no tienen efecto (código migró a Brevo HTTP):

- `DEFAULT_FROM_EMAIL`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_PORT`, `EMAIL_USE_SSL`, `EMAIL_USE_TLS`, `RESEND_API_KEY`

---

## D-016 — Roadmap de lanzamiento público

**Fecha:** 2026-05-11

Hoja de ruta para preparar la app para usuarios reales. Ítems ordenados por prioridad y dependencias.

**Prerequisito bloqueante:** DT-001 resuelto con Brevo API (Render Free bloquea SMTP; se usa HTTP API en su lugar).

### RL-001 — Recuperar contraseña (P0)

**Estado:** ✅ Resuelto (v0.25.0)

Flujo completo implementado con `BrevoPasswordResetView` que envía via Brevo API HTTP para evitar el bloqueo SMTP de Render Free. Probado en producción.

### RL-002 — Landing page pública (P1)

**Estado:** ✅ Resuelto (e11b874)

Vista pública en `/` que muestra la app a usuarios no autenticados. Los autenticados redirigen al dashboard.

**Tareas:**

- `LandingView` en `apps/core/views.py`
- Template `templates/core/landing.html` con hero, features y CTA
- Lógica de redirección en `apps/reports/views.py`
- Secciones: hero, features (Gastos/Ingresos/Ahorros/Dashboard), CTA registro/login, footer con links legales

### RL-003 — Términos y condiciones (P1)

**Estado:** ✅ Resuelto (v0.26.0)

**Tareas:**

- `TermsView` + URL `/terms/` en `apps/core/`
- Template `templates/core/terms.html`
- Checkbox "Acepto los términos" en formulario de registro (`apps/users/forms.py`)
- Links en footer (`templates/base.html`) y página de registro

**Contenido clave:** uso personal no comercial, no somos asesores financieros, datos en servidores de Render, derecho a eliminar cuenta.

### RL-004 — Política de privacidad (P1)

**Estado:** ✅ Resuelto (v0.26.0)

**Tareas:**

- `PrivacyView` + URL `/privacy/` en `apps/core/`
- Template `templates/core/privacy.html`
- Link en footer

**Contenido clave:** qué datos se recopilan (email, transacciones), cómo se usan (solo para la app), no se venden datos, cómo eliminar cuenta, cookies (sesión y CSRF).

### RL-005 — Confirmación de email (P1)

**Estado:** ✅ Resuelto (v0.28.0)

**Implementación:**

- Campo `email_verified` en `apps/users/models.py` + migración `0002_email_verified.py`
- `apps/users/tokens.py` — `EmailVerificationTokenGenerator` basado en `PasswordResetTokenGenerator`; el token se invalida automáticamente al verificar (el hash incluye `email_verified`)
- `_send_verification_email()` en `apps/users/views.py` — envía link via Brevo API; link válido 7 días
- `VerifyEmailView` — GET con `uidb64` + `token`; setea `email_verified=True` y redirige
- `ResendVerificationView` — reenvío manual desde dashboard
- Banner en `base.html` para usuarios no verificados

**Flujo:** Registro → email con link → click → `email_verified=True` → banner desaparece

### RL-006 — Backup automático de DB (P1)

**Estado:** ✅ Resuelto (v0.27.0)

Debe implementarse **antes del lanzamiento**, no después. Pérdida de datos en el primer día sería catastrófica.

**Tareas:**

- Script `scripts/backup_db.sh` con `pg_dump` + subida a S3 o Cloudflare R2
- GitHub Action con cron diario (`.github/workflows/backup.yml`)
- Documentar proceso de restore en `docs/BACKUP.md`

**Alternativa:** Render plan pago ($7/mes) incluye backups automáticos — evaluar según costo vs. complejidad.

### RL-007 — Email de bienvenida (P2)

**Estado:** ✅ Resuelto (v0.30.0)

**Implementación:**

- Template `templates/users/emails/welcome.txt` con tips de uso (registrar gasto, categorías, presupuestos, metas)
- `_send_welcome_email(user)` en `apps/users/views.py` — envía via Brevo API
- Llamado desde `VerifyEmailView` solo en la primera verificación exitosa

### RL-008 — Tour / guía inicial (P2)

**Estado:** ✅ Resuelto (v0.32.0 — Shepherd.js)

**Tareas:**

- Campo `has_seen_tour` en `apps/users/models.py`
- Integrar Shepherd.js o librería similar
- Definir pasos: dashboard → registrar gasto → metas de ahorro → categorías
- Activar en primer login, botón "Ver tour de nuevo" en perfil

**Orden de ejecución sugerido:**

```text
Prerequisito:  DT-001 — dominio verificado en Resend

Semana 1:      RL-001 Recuperar contraseña
               RL-003 Términos y condiciones
               RL-004 Política de privacidad

Semana 2:      RL-006 Backup DB  ← antes del lanzamiento
               RL-002 Landing page
               RL-005 Confirmación de email

Semana 3:      RL-007 Email de bienvenida
               RL-008 Tour inicial
```

**Checklist pre-lanzamiento consolidado** _(actualizado 2026-05-12)_

#### ✅ Completado

- [x] Recuperar contraseña (RL-001) — `ca5ce04`
- [x] Landing page pública (RL-002) — `e11b874`
- [x] Términos y condiciones (RL-003) — `3746b96`
- [x] Política de privacidad (RL-004) — `3746b96`
- [x] Checkbox aceptación en registro — `3746b96`
- [x] Seguridad prod: DEBUG=False, SECRET_KEY, ALLOWED_HOSTS
- [x] Healthcheck `/healthz/` con throttling
- [x] Sentry para errores
- [x] `check --deploy` en CI (ci.yml línea 189)
- [x] Rate limiting (django-axes)
- [x] CSP headers
- [x] HTTPS hardening (HSTS, cookies secure)

#### P0 — Bloqueantes

- [x] `render.yaml` versionado en repo (config declarativa de deploy) — resuelto v0.29.0
- [x] Docs email unificados (README actualizado para reflejar Brevo) — resuelto v0.29.0

#### P1 — Muy recomendados

- [x] Confirmación de email al registrarse (RL-005) — resuelto v0.28.0
- [x] Backup automático de DB (RL-006) — workflow diario a Cloudflare R2, probado en producción
- [x] Smoke tests post-deploy — resuelto v0.31.0 (`.github/workflows/smoke.yml`)
- [x] SLA mínimo documentado (qué esperar en plan free) — resuelto v0.31.0 (README)

#### P2 — Nice to have

- [x] Email de bienvenida (RL-007) — resuelto v0.30.0
- [x] Tour / guía inicial (RL-008) — resuelto v0.32.0 (Shepherd.js)
- [ ] Prueba de restore de backup — 1 hora

#### Verificaciones manuales

- [x] URL de Render funcionando — confirmado en QA (2026-05-13)
- [x] Variables de entorno en Render correctas — confirmado en QA (2026-05-13)
- [ ] Brevo: dominio verificado, SPF/DKIM configurado
- [ ] Probar envío real de email (verificación + reset password) — requiere acceso a bandeja real
- [ ] Probar registro completo como usuario nuevo (email verificación + bienvenida)
- [ ] Probar en mobile (tour + navegación general)

---

## D-018 — Gastos Compartidos: modelo sin cuenta para el miembro

**Fecha:** 2026-06-01
**Estado:** ✅ Implementado (v1.6.0)

### Contexto
Se necesitaba un módulo para que una persona registre gastos del hogar indicando quién pagó cada cosa (ej: Nico pagó la luz, Pedro pagó el super).

### Decisión
Implementar `HouseholdMember` como un modelo simple de nombre, sin cuenta en la app. El dueño de la cuenta registra todos los gastos y asigna el pagador.

### Justificación
- Cubre el 90% del caso de uso sin la complejidad de invitaciones, tokens de aceptación y permisos multi-usuario.
- El miembro no necesita cuenta para que el registro sea útil — la app es una herramienta de registro personal, no colaborativa.
- Si en el futuro hay demanda de que el miembro cargue sus propios gastos, el modelo `HouseholdMember` puede evolucionar a un sistema de invitación por email vinculando a un `User`.

### Riesgo aceptado
El miembro no puede cargar gastos por su cuenta ni ver el historial. Si el dueño de la cuenta borra un miembro, los gastos quedan sin pagador asignado (campo `paid_by` en NULL). Aceptable para el MVP.
