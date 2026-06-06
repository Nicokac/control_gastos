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

**Estado:** ⏳ Pendiente

La app web usa el ícono genérico de Bootstrap Icons (`bi-wallet2`) y no tiene favicon personalizado. La app mobile usa `Icons.account_balance_wallet` de Material Design en la pantalla de login. Ninguna de las dos tiene un ícono propio que identifique la marca.

**Why:** se detectó al desarrollar la app mobile que la identidad visual carece de un ícono propio. El ícono del sistema es funcional pero no diferencia la app.

**Camino de resolución:** diseñar o elegir un ícono SVG representativo, usarlo como favicon en la web (`staticfiles/`), reemplazar el ícono en la pantalla de login de la web y en la pantalla de login de Flutter, y generarlo en los tamaños necesarios para el launcher de Android/iOS (`flutter_launcher_icons`).

### DT-049 — Mobile: deshacer "marcar pagado" en gastos fijos

**Estado:** ⏳ Pendiente

Al marcar un gasto fijo como pagado desde la app mobile, se crea un `Expense` vinculado al recurrente. No existe forma de revertir esta acción desde la app — el usuario debe ir a la lista de Gastos y eliminar el registro manualmente.

**Why:** acción detectada durante el desarrollo de `recurring_list_screen.dart`. No hay endpoint `unmark-paid` en la API.

**Camino de resolución:** agregar endpoint `POST /api/v1/recurring/{id}/unmark-paid/` en `RecurringExpenseViewSet` que elimine el último `Expense` del mes actual vinculado al recurrente. Exponer el botón en la app mobile solo cuando el estado del recurrente es `paid` en el mes actual.

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
