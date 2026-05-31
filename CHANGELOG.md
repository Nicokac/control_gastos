# Changelog

Todas las versiones notables de este proyecto están documentadas aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [1.5.0] — 2026-05-31

### Added

- **Mi cuenta**: campo "Inicio del mes financiero (día)" — configurá el día en que empieza tu período (1-28, default 1).
- **Dashboard**: gastos e ingresos del período se calculan sobre el rango financiero configurado (ej: del 10/05 al 09/06 si el inicio es día 10).
- **Dashboard**: el texto "Día X de Y" debajo de la barra de progreso es clickeable y lleva a Mi Perfil. Muestra "(período financiero)" cuando el inicio es distinto al día 1.

---

## [1.4.9] — 2026-05-30

### Added

- **Dashboard**: alerta visual (amarilla/roja) cuando los gastos superan el umbral configurado por el usuario. La barra de progreso cambia de color según el umbral.
- **Mi cuenta**: campo "Umbral de alerta (%)" en preferencias (default 80). Configurable entre 1 y 100.
- **Gastos / Ingresos**: el campo cotización USD se pre-completa con el último valor usado por el usuario al seleccionar USD en el formulario.

---

## [1.4.8] — 2026-05-30

### Added

- **Ingresos Fijos**: nuevo módulo `apps/recurring_income` para modelar ingresos periódicos (sueldo, alquiler, freelance mensual). CRUD completo con estados por mes (cobrado/pendiente/vencido).
- **Ingresos Fijos**: botón "Registrar cobro" pre-completa el formulario de ingreso con categoría y descripción. El cobro queda vinculado al ingreso fijo via FK.
- **Ingresos Fijos**: toggle para ocultar/mostrar inactivos, igual que Gastos Fijos.
- **Sidebar**: nueva entrada "Ingresos Fijos" bajo PLANIFICACIÓN.

---

## [1.4.7] — 2026-05-30

### Added

- **Gastos Fijos**: soporte para gastos en cuotas — campos opcionales "Cantidad de cuotas" y "Mes de inicio". Al registrar el último pago, el gasto se desactiva automáticamente.
- **Gastos Fijos**: badge de progreso en la lista ("cuota 3/12") visible en gastos con cuotas definidas.
- **Gastos Fijos**: inactivos ocultos por defecto con toggle "Mostrar inactivos (N)" en el header de la tabla.

---

## [1.4.6] — 2026-05-22

### Added

- **Gastos**: gráfico de línea "Acumulado del mes" en el panel "Ver resumen", visible cuando hay un mes específico filtrado. Muestra el gasto acumulado día a día con tooltip por día.
- **General**: cache busting en todos los archivos JS estáticos via `?v={{ APP_VERSION }}` — evita que el browser sirva versiones desactualizadas tras un deploy.

---

## [1.4.5] — 2026-05-22

### Added

- **Gastos**: donut chart de distribución por grupo en el panel "Ver resumen". Agrupa por categoría de primer nivel (no subcategoría). Segmentos < 3% se fusionan en "Otros".
- **Gastos**: leyenda por grupo con dot de color sincronizado, porcentaje, monto y barra de ranking horizontal. Click en un ítem filtra la tabla al grupo.
- **Gastos**: card de leyenda scrolleable con fade inferior indicador de contenido oculto.
- **Gastos**: tipo de gasto y método de pago en el resumen ahora muestran porcentaje y barra de progreso, ordenados por monto descendente.

---

## [1.4.4] — 2026-05-21

### Added

- **Ingresos**: desglose por categoría en panel "Ver resumen" del período.
- **Ingresos**: filtros de monto mínimo y máximo en la lista.

---

## [1.4.3] — 2026-05-21

### Added

- **Gastos**: desglose por categoría individual en el panel "Ver resumen", ordenado por monto descendente con nombre del grupo padre.
- **Gastos**: filtros de monto mínimo y máximo en la fila de filtros de la lista.
- **Gastos**: método de pago y tipo de gasto siempre visibles en el formulario (sin collapse).
- **Gastos**: vista de detalle muestra siempre método de pago y tipo, con link "Completar" cuando están vacíos.

---

## [1.4.2] — 2026-05-21

### Added

- **Dashboard**: botones de editar y eliminar en cada fila de últimas transacciones, sin salir del dashboard.
- **Dashboard**: links "Ver gastos" y "Ver ingresos" en el header de últimas transacciones, filtrados al período actual.
- **Dashboard**: puntos del gráfico de evolución clickeables — navegan al dashboard de ese mes.

---

## [1.4.1] — 2026-05-21

### Added

- **Gastos / Ingresos**: headers de tabla clickeables para ordenar por Fecha, Categoría, Descripción o Monto. Clic repetido invierte la dirección. El header activo muestra un chevron indicador.
- **Formulario Gasto / Ingreso**: campo de búsqueda sobre el picker de categorías — filtra en tiempo real ocultando los botones que no coinciden y colapsa grupos vacíos. Incluye botón `×` para limpiar.

---

## [1.4.0] — 2026-05-21

### Added

- **Categorías**: búsqueda en tiempo real independiente por sección — campo dentro de cada card (Gastos / Ingresos) que filtra grupos y subcategorías por nombre sin request al servidor.
- **Categorías**: botón `×` para limpiar el campo de búsqueda.
- **Categorías**: los grupos de sistema se redujeron a uno por tipo — "Sin clasificar" (Gastos) y "Sueldo" (Ingresos). Ambos permiten agregar subcategorías de usuario.

### Fixed

- **Categorías**: el link "Agregar subcategoría" ahora aparece también en grupos de sistema.

---

## [1.3.0] — 2026-05-21

### Added

- **Dashboard**: navegación por período con flechas `‹` `›` — todos los KPIs, distribución y gastos fijos responden al mes seleccionado. La flecha derecha y el botón "Hoy" solo aparecen cuando no se está en el mes actual.
- **Dashboard**: card de Ahorro integrada en la fila de KPIs junto a Gastos e Ingresos, con total acumulado, barra de progreso y cantidad de metas activas.
- **Dashboard**: cards de Gastos e Ingresos clickeables (link a lista filtrada por mes).
- **Dashboard**: badges de gastos fijos pendientes debajo de la barra de progreso.
- **Dashboard**: barra de balance muestra día del mes y monto disponible restante.
- **Gastos**: búsqueda por nombre de categoría y grupo además de descripción (Q filter).
- **Gastos**: botón duplicar precarga todos los campos del gasto original en el formulario.
- **Gastos**: filtros de método de pago y tipo siempre visibles (eliminado el collapse "Más filtros").
- **Gastos**: estado vacío diferencia entre sin datos y sin resultados para filtros activos.
- **Ingresos**: paridad con Gastos — duplicar, modal de eliminación con confirmación, búsqueda por categoría/grupo, estado vacío diferenciado, fecha en `d/m/Y`, grupo visible sobre el badge.
- **General**: botón "← Volver" contextual en todas las listas (Gastos, Ingresos, Ahorro, Gastos Fijos, Categorías) — visible solo cuando hay referrer del mismo dominio.

### Fixed

- **General**: mensajes de error en formularios de depósito y movimiento de ahorro unificados al patrón estándar de la app.

---

## [1.2.1] — 2026-05-21

### Fixed

- **Dashboard**: ícono del widget Gastos cambiado de `bi-exclamation-triangle` a `bi-arrow-up-circle`.
- **Dashboard**: la barra de progreso y el texto "Gastaste el X% de tus ingresos" ya no aparecen cuando no hay ingresos registrados en el mes — se muestra un mensaje explicativo en su lugar.
- **Dashboard**: las últimas 5 transacciones ahora muestran el ícono y nombre de categoría de cada movimiento.
- **General**: el botón flotante `+` ahora apunta a la acción correcta según la sección activa — Ingresos, Ahorro, Gastos Fijos o Categorías — en lugar de siempre crear un Gasto.
- **General**: al intentar guardar un Gasto o Ingreso sin seleccionar categoría, aparece el mensaje "Seleccioná una categoría." debajo del grid y desaparece al seleccionar.
- **General**: el botón de submit ya no queda bloqueado en "Procesando..." cuando la validación del formulario falla en el cliente.
- **General**: el botón Cancelar usa el mismo estilo (`btn-outline-secondary` con ícono `×`) en todos los formularios.
- **General**: las fechas en Gastos Fijos y Mi Perfil se mostraban en inglés ("May 2026") — corregido a español y formato numérico (`d/m/Y`).
- **General**: el toast de confirmación mostraba el guion como escape unicode — corregido cambiando el encoding del data attribute.

---

## [1.2.0] — 2026-05-18

### Added

- **Categorías**: el selector de grupo padre filtra automáticamente al elegir el tipo — al seleccionar Gasto solo aparecen grupos de gasto, al seleccionar Ingreso solo grupos de ingreso. Implementado via `CategoryTypeSelect` (widget con `data-type` en cada `<option>`) y `category_form.js` (archivo externo para cumplir con CSP).

### Fixed

- **Categorías**: "Agregar subcategoría" ya no aparece en grupos de Sistema.
- **Categorías**: la validación de nombres duplicados detecta correctamente conflictos con categorías de Sistema y entre categorías del propio usuario.

---

## [1.1.1] — 2026-05-17

### Fixed

- **Categorías**: el botón flotante de nuevo gasto ya no aparece en la pantalla de categorías.
- **Categorías**: cada grupo muestra el contador de subcategorías `(N)` en el encabezado.
- **Categorías**: "Agregar subcategoría" ya no aparece en grupos de Sistema — esos grupos no son editables por el usuario.
- **Categorías**: la validación de nombres duplicados ahora detecta correctamente conflictos con categorías de Sistema y entre categorías del propio usuario. Había un bug silencioso donde `category_type` se resolvía antes de que el campo `type` fuera validado, dejando la query con tipo vacío.

---

## [1.1.0] — 2026-05-17

### Added

- **Novedades**: historial pre-lanzamiento agrupado en desplegable colapsable para no sobrecargar la pantalla.

### Fixed

- **Montos**: todos los campos de monto ahora usan formato argentino (coma decimal, punto de miles) — `1.234,50` — en Gastos, Ingresos y Ahorro. El placeholder mostraba `0.00` con punto, ahora muestra `0,00`.
- **Auth**: GET directo a `/users/logout/` redirigía con 403 en Django 5.x — ahora redirige al login.
- **Templates**: `{% endblock content %}` incorrecto en `privacy.html` causaba 500 en producción para usuarios no autenticados.

---

## [1.0.0] — 2026-05-13

### Added

- **Lanzamiento v1.0** — primera versión estable con todas las funciones principales: dashboard, gastos, ingresos, ahorro, categorías, gastos fijos, tour interactivo y verificación de email.

---

## [0.32.0] — 2026-05-13

### Added

- **Tour interactivo** — al acceder al dashboard por primera vez, Shepherd.js guía al usuario por las secciones clave: Dashboard, Gastos, botón de Nuevo Gasto, Ahorro y Categorías. El tour se puede relanzar desde Mi Perfil → "Ver tour de nuevo". Cubre RL-008.

### Fixed

- **`/terms/` y `/privacy/` vacíos para usuarios logueados** — los templates usaban `{% block auth_content %}` que solo se renderiza para usuarios no autenticados. Cambiado a `{% block content %}` con navbar condicional: muestra "Ir al dashboard" si está logueado y "Iniciar sesión / Crear cuenta" si no.
- **Tour en mobile** — en viewport < 768px el sidebar está oculto. Los pasos del tour que apuntaban a elementos del sidebar ahora usan `attachTo: null`, haciendo que Shepherd centre el popup en pantalla en lugar de posicionarlo en coordenadas 0,0.

---

## [0.31.0] — 2026-05-12

### Added

- **Smoke tests post-deploy** — GitHub Action (`.github/workflows/smoke.yml`) que se dispara en cada push a `main` y verifica que `/healthz/`, `/`, `/users/login/`, `/users/register/`, `/terms/` y `/privacy/` responden 200 en producción. Requiere el secret `PRODUCTION_URL` con la URL de Render. Cierra P1.

---

## [0.30.0] — 2026-05-12

### Added

- **Email de bienvenida** — al verificar el email, el usuario recibe un mensaje de bienvenida con tips de uso: cómo registrar gastos, crear categorías, armar presupuestos y usar metas de ahorro. Cubre RL-007.

---

## [0.29.0] — 2026-05-12

### Added

- **`render.yaml` versionado** — configuración declarativa de Render en el repositorio: servicio web, DB PostgreSQL, variables de entorno y healthcheck. Elimina dependencia de configuración manual en la UI de Render. Cierra P0.

### Fixed

- **Docs email unificados** — el README mencionaba Resend como proveedor de email. Actualizado para reflejar Brevo API como único proveedor transaccional (reset, verificación, feedback). Cierra P0.

---

## [0.28.0] — 2026-05-12

### Added

- **Confirmación de email** — al registrarse, el usuario recibe un email con un link para verificar su cuenta. El link usa un token firmado válido por 7 días que se invalida automáticamente tras ser usado. Cubre RL-005.
- **Banner de verificación pendiente** — usuarios con email sin verificar ven un aviso persistente en el encabezado con un botón para reenviar el email de verificación.

---

## [0.27.0] — 2026-05-13

### Added

- **Backup automático de DB** — GitHub Action con cron diario (03:00 UTC) que hace `pg_dump` de PostgreSQL y sube el archivo a Cloudflare R2. Retención indefinida en el free tier (10GB). Cubre RL-006.

---

## [0.26.0] — 2026-05-11

### Added

- **Términos y condiciones** — página pública en `/terms/` con condiciones de uso, responsabilidades y derecho a eliminar cuenta. Cubre RL-003.
- **Política de privacidad** — página pública en `/privacy/` con detalle de datos recopilados, uso, almacenamiento y cookies. Cubre RL-004.
- **Checkbox de aceptación** — el formulario de registro ahora requiere aceptar los términos y condiciones antes de crear la cuenta.
- **Links legales en footer** — la landing, términos y privacidad incluyen links a ambas páginas en el footer.

---

## [0.25.0] — 2026-05-11

### Added

- **Recuperar contraseña** — flujo completo para resetear la contraseña desde el login. El usuario ingresa su email, recibe un link por email (válido 24 horas) y elige una nueva contraseña. Cubre RL-001.
- **Email via Brevo** — los emails transaccionales ahora se envían via Brevo API HTTP, reemplazando Resend que requería dominio propio verificado. Render Free bloquea SMTP; la API HTTP no tiene esa restricción. Cubre DT-001.

---

## [0.24.0] — 2026-05-11

### Added

- **Dashboard — widget de Gastos Fijos** — nuevo card que muestra cuántos gastos fijos fueron pagados sobre el total activo del mes, con barra de progreso y badge de vencidos. El color del card refleja el estado: verde (todos pagados), rojo (hay vencidos), azul (en curso). Solo visible si el usuario tiene gastos fijos activos. Cubre DT-009.

### Fixed

- **Gastos Fijos — tooltips en íconos de estado** — los íconos de pagado, pendiente, vencido e inactivo ahora muestran tooltips de Bootstrap al hacer hover, reemplazando el `title` nativo del browser. Cubre DT-010.

---

## [0.23.0] — 2026-05-10

### Added

- **Gastos Fijos** — nueva sección para registrar servicios, impuestos, cuotas y cualquier gasto mensual recurrente. Cada gasto fijo muestra su estado (pagado ✅, pendiente ⏰, vencido ❗) y el último pago registrado.
- **Registrar pago desde Gastos Fijos** — el botón "Registrar pago" pre-completa el formulario de gasto con la categoría y descripción del gasto fijo, y al guardar redirige de vuelta a la lista de gastos fijos con el estado actualizado.
- **Resumen del mes** — barra de progreso que muestra cuántos gastos fijos fueron pagados sobre el total activo del mes corriente.

### Fixed

- **Toast post-pago** — el mensaje de confirmación ahora se muestra correctamente al volver a la lista de gastos fijos tras registrar un pago.
- **Mensaje duplicado al eliminar** — se eliminó el banner inline que duplicaba el toast de confirmación en toda la app.

---

## [0.22.0] — 2026-05-10

### Added

- **Gastos e Ingresos — exportación CSV** — nuevo botón para descargar el historial del período actual como archivo CSV, respetando los filtros aplicados. Cubre DT-008.

---

## [0.21.0] — 2026-05-10

### Added

- **Categorías — reordenamiento manual de grupos** — los grupos de categorías ahora se pueden arrastrar para cambiar su orden de visualización. El orden persiste en base de datos. Cubre DT-006.

---

## [0.20.0] — 2026-05-10

### Added

- **Categorías — grupos colapsables** — cada grupo puede expandirse y contraerse haciendo clic en el encabezado. El estado de cada grupo persiste en localStorage entre visitas.

### Changed

- **Gastos — orden de columnas en la tabla** — las columnas se reordenaron a Fecha → Categoría → Descripción → Monto para priorizar el clasificador principal sobre el detalle.

---

## [0.19.0] — 2026-05-10

### Added

- **Gastos e Ingresos — búsqueda por texto en el listado** — nuevo campo "Buscar" en el formulario de filtros de ambos listados. Filtra por descripción (sin distinción de mayúsculas) y se puede combinar con los demás filtros existentes (mes, año, categoría, etc.).

---

## [0.18.0] — 2026-05-10

### Fixed

- **Sidebar mobile — comportamiento en rotación y navegación** — el offcanvas mobile ahora se cierra automáticamente al tocar un link de navegación. Al rotar el dispositivo de portrait a landscape, el offcanvas y su backdrop se limpian correctamente sin bloquear la interfaz.

---

## [0.17.0] — 2026-05-10

### Added

- **Tests — cobertura de mensajes toast en CRUD** — se agregaron tests de integración que verifican los mensajes de confirmación al crear, editar y eliminar registros en Gastos, Categorías y Ahorro. Se corrigió el test de eliminación de Ingresos que no aserteaba el contenido del mensaje. Cubre DT-004 de la deuda técnica registrada.

### Docs

- **DECISIONS.md** — se registraron los ítems de deuda técnica no registrada: DT-004 (resuelto), DT-005 (sidebar mobile), DT-006 (orden de categorías), DT-007 (búsqueda por texto), DT-008 (exportación CSV).

---

## [0.16.0] — 2026-05-10

### Added

- **Dashboard — selector de año en evolución mensual** — nuevo selector en el encabezado del gráfico. Al elegir un año anterior se muestran los 12 meses completos; para el año actual, enero hasta el mes en curso. Los años disponibles se calculan desde el primer año con datos del usuario.

### Changed

- **Healthz — throttle migrado a Django cache** — el rate limiting de `/healthz/` deja de usar un `dict` en memoria y pasa a `django.core.cache`. Comportamiento idéntico con `LocMemCache`; para escalar a múltiples workers solo se cambia el backend a Redis sin tocar la lógica.

---

## [0.15.0] — 2026-05-10

### Added

- **Badge de Novedades dinámico** — la versión ya no está hardcodeada en el JS. Se inyecta desde el servidor via context processor `app_version` → `window.APP_VERSION`. El badge "Nuevo" se actualiza automáticamente con cada deploy sin tocar código JS.

### Changed

- **Novedades — texto accesible con contexto de sección** — cada item ahora indica en qué parte de la app ocurrió el cambio (ej: "Gastos: el monto ya no aparece vacío...") y usa lenguaje sin términos técnicos.

---

## [0.14.0] — 2026-05-10

### Fixed

- **Feedback — sin confirmación visual tras envío** — los mensajes Django (`messages.success`) no se renderizaban en ningún lado. Se inyectan ahora como `window.DJANGO_MESSAGES` en `base.html` y `initSessionToasts()` los consume disparando `showToast()`. Aplica a toda la app, no solo feedback.
- **Feedback — error de validación persiste al escribir** — el mensaje "Este campo es obligatorio" permanecía visible mientras el usuario escribía. Se limpia al detectar contenido vía evento `input`.
- **Feedback — round-trip innecesario con campo vacío** — el form se enviaba al servidor mostrando "Procesando..." sin validar primero. Ahora el JS intercepta el submit, previene el envío si el textarea está vacío y mantiene el foco en el campo.

---

## [0.13.0] — 2026-05-10

### Added

- **Mi Cuenta — eliminar cuenta** — nueva sección "Zona de peligro" en el perfil con confirmación antes de borrar. Elimina el usuario y todos sus datos en cascada, cierra la sesión y redirige al login.

### Fixed

- **Mi Cuenta — último acceso en hora local** — se aplicaba `date` en UTC. Corregido con `|localtime` para convertir a `America/Argentina/Buenos_Aires` antes de formatear.

---

## [0.12.0] — 2026-05-09

### Changed

- **Categorías — selector de color visual** — reemplazado `input[type=color]` nativo del browser por grilla de 10 círculos predefinidos (igual que Ahorro). Paleta definida en `CATEGORY_COLOR_CHOICES` en `constants.py`. El color se pre-carga correctamente al editar.
- **Categorías — copy del botón** — "Nuevo Grupo" renombrado a "Nueva Categoría" para que coincida con el formulario al que lleva.
- **Mi Cuenta — nombre y apellido no se pre-cargan** — el template renderizaba `<input>` manualmente con `{{ form.first_name.value }}`, que devuelve cadena vacía si el campo no fue completado nunca. Corregido usando `{{ form.first_name }}` para delegar el render al widget del form, que vincula correctamente el valor de la instancia.

---

## [0.11.0] — 2026-05-09

### Fixed

- **Ingresos — total del período mostraba $0** — el contexto usaba `total_amount` pero el template leía `total`. Renombrado.
- **Ingresos — categorías vacías en formularios y listado** — `get_income_categories` filtraba solo subcategorías (`parent__isnull=False`), pero las categorías de ingreso del sistema son de un solo nivel. Ahora retorna todas las INCOME sin restricción de parent.
- **Categorías de ingreso no visibles en `/categories/`** — `_build_full_tree` excluía grupos del sistema sin subcategorías. Corregido incluyendo todos los grupos.
- **Ahorro — monto objetivo vacío al editar** — `SavingForm` no vinculaba `target_amount` desde la instancia al ser un campo fuera de `Meta`. Corregido seteando `initial` en `__init__`.
- **Ahorro — color sin pre-seleccionar al editar** — `icon` y `color` son `ChoiceField` declarados fuera de `Meta`; Django no los vincula automáticamente. Corregido en `__init__`.
- **Ahorro — copy "Antes de crearla" en modo edición** — corregido con `{% if is_edit %}`.

---

## [0.10.0] — 2026-05-09

### Fixed

- **Monto vacío al editar gasto/ingreso** — `CurrencyFormMixin` reemplazaba el campo `amount` con `ARSDecimalField` sin preservar el valor de la instancia, dejando el campo vacío en edición. Corregido pasando `instance.amount` como `initial` al nuevo campo.
- **Resumen sin "Sin clasificar"** — el panel "Ver resumen" ignoraba los gastos sin tipo/método asignado. Ahora incluye una fila "Sin clasificar" con el monto restante cuando corresponde.

---

## [0.9.0] — 2026-05-09

### Added

- **Sidebar mobile** — en pantallas pequeñas el sidebar se abre como offcanvas (Bootstrap) desde un botón hamburguesa en el navbar. Comparte la misma navegación que el sidebar desktop via partial `sidebar_nav.html`.
- **Rate limiting en `/healthz/`** — throttle en memoria: máx 10 requests por IP en ventana de 60 segundos, retorna HTTP 429. Sin dependencias extra (D-004).

---

## [0.8.0] — 2026-05-09

### Added

- **Sidebar colapsable** — botón "Contraer/Expandir" que reduce el sidebar a íconos (64px). Estado persistido en `localStorage`. Animación CSS suave (`transition: width/margin-left 0.2s`).

### Fixed

- **Layout sin overflow horizontal** — reemplazado `container-fluid > row` por `div.app-layout` con `display: flex`. El `main` usa `flex: 1 + min-width: 0` en lugar de heredar `100vw` del grid de Bootstrap, eliminando el scroll horizontal espurio.
- **Responsive del main al colapsar sidebar** — el área de contenido ahora se expande correctamente cuando el sidebar se colapsa (64px) y se contrae cuando se expande (280px), en desktop. En mobile el sidebar pasa a `position: relative` y el main ocupa el ancho completo.

---

## [0.7.0] — 2026-05-09

### Corregido

- **Feedback via Resend API HTTP** — el envío de email del formulario de feedback fallaba en Render Free tier porque bloquea conexiones SMTP salientes (puertos 25, 465, 587). Migrado de `send_mail()` a `resend.Emails.send()` via API HTTP (puerto 443). Dependencia `resend` agregada a `requirements/prod.txt`.
- **Cambio de día a las 21hs** — reemplazado `timezone.now().date()` por `timezone.localdate()` en vistas, formularios, utils y modelos. La app ahora usa la fecha local de Argentina (UTC-3) en lugar de UTC.

---

## [0.6.0] — 2026-05-08

### Added
- **Jerarquía de categorías** — modelo grupo → subcategoría con FK self (`parent`). Los gastos se asignan a subcategorías; los grupos son agrupadores visuales (Fases 1–5).
- **Selector agrupado en formularios** — radio buttons de categorías agrupados bajo cabecera de grupo en formularios de gastos e ingresos (Fase 2).
- **Dashboard drill-down** — ranking de categorías expandible por grupo para ver desglose por subcategoría. Donut agrupado por grupo padre (Fase 3).
- **Filtro por grupo en lista de gastos** — selector de grupo + selector dinámico de subcategoría (JS con `data-parent`). La subcategoría tiene prioridad sobre el grupo al filtrar (Fase 4).
- **Mover subcategorías entre grupos** — campo `parent` visible al editar subcategorías; `?parent=<pk>` pre-selecciona el grupo en creación (Fase 5).

### Fixed
- **Constraint de unicidad de categorías** — reemplazada constraint `(name, user, type)` por dos constraints condicionales: una para grupos (`parent IS NULL`) y otra para subcategorías (`parent IS NOT NULL`), permitiendo nombres iguales en grupos y subcategorías distintas.
- **Cambio de día a las 21hs** — reemplazado `timezone.now().date()` por `timezone.localdate()` en todas las vistas, formularios y utils. La app ahora usa la fecha local de Argentina (UTC-3) en lugar de UTC.

### Changed
- "Ranking de Grupos" renombrado a "Ranking de Categorías" en el dashboard.
- Dashboard: distribución de gastos ahora agrupa por grupo padre con fallback a subcategoría para categorías sin jerarquía.

---

## [0.5.0] — 2026-05-04

### Added
- **Formulario de feedback** — sección "Reportar / Sugerir" en el sidebar. Envía email al administrador con tipo de reporte, mensaje y datos del usuario. Implementado en `apps.core` sin modelo de DB (D-010).
- **Gráfico de evolución mensual** — línea con 4 series (Ingresos, Gastos, Ahorro, Balance) desde enero hasta el mes actual. Balance con línea punteada (D-008).
- **Dashboard rediseñado** — Balance como card hero con barra de progreso y comparación porcentual vs mes anterior. Donut + ranking de categorías con scroll.
- **Picker visual de íconos** — selector de íconos con radio buttons en formularios de categorías y metas de ahorro.
- **Filtros avanzados de gastos** — filtro por método de pago y tipo de gasto (fijo/variable) con resumen colapsable.
- **Vinculación gasto → meta de ahorro** — al registrar un gasto se puede seleccionar una meta como destino; el monto se deposita automáticamente.
- **Formato ARS en campos de monto** — acepta coma como separador decimal en formularios.

### Fixed
- CSP: habilitado `unsafe-inline` en `style-src` para styles dinámicos del dashboard (D-009).
- Barra de progreso del balance usa clases Bootstrap en lugar de inline color.
- `format_currency()` centralizado en filtro de template.

---

## [0.4.0] — 2026-03-29

### Removed
- **Módulo de presupuestos** (`apps.budgets`) eliminado por completo — vistas, formularios, admin, templates, fixtures, tests y referencias en dashboard/sidebar/perfil (D-007).

---

## [0.3.0] — 2026-03-08

### Added
- **Rate limiting** con django-axes: 5 intentos fallidos → bloqueo 2 horas. Página `account_locked` dedicada.
- **Headers de seguridad** — HSTS, CSP, X-Frame-Options, SESSION/CSRF cookies seguras en prod.
- **Logging estructurado** — eventos de seguridad, performance (RequestTimingMiddleware) y errores.
- **Error tracking** con Sentry (prod).
- **Comando `generate_secret_key`** — genera SECRET_KEY segura con opción `--env-format`.
- **Comando `axes_status`** — muestra y limpia intentos de login fallidos.
- **Comando `view_logs`** — consulta logs por tipo (security, error, app).
- **Healthcheck** `/healthz/` — verifica DB y retorna 200/503.
- **Índices compuestos** en Expense, Income, Saving, Category para queries frecuentes.
- **Constraints de DB** en Category: `system_category_no_user`, `user_category_requires_user`.

### Fixed
- `alert_threshold` del User se usa como default en cada Budget (D-003).
- Income: unificado filtrado de fechas con `get_month_date_range_exclusive`.
- Login redirige al dashboard en lugar de categories.
- Eliminado `MEDIA_ROOT` sin definir y comentarios muertos.

### Changed
- Sidebar: "Configuración" → "Mi cuenta".
- "Nuevo Gasto" estandarizado en toda la UI.

---

## [0.2.0] — 2026-02-17

### Added
- **Metas de ahorro** (`apps.savings`) — crear metas con objetivo y fecha límite, registrar depósitos y retiros, seguimiento de progreso porcentual, auto-completado al llegar al objetivo.
- **Multimoneda** — soporte ARS/USD con tipo de cambio configurable. `amount_ars` calculado en Python via `CurrencyMixin.save()` (D-001).
- **Dashboard** — balance mensual, comparación con mes anterior, últimas transacciones, distribución de gastos por categoría.
- **Categorías personalizadas** — CRUD de categorías por usuario, iconos y colores, tipos Gasto/Ingreso.
- **Paginación** en listados de gastos, ingresos y metas.
- **CI/CD** con GitHub Actions — lint, tests, coverage ≥80%, security checks, django-checks, collectstatic, deploy a Render.
- **Pre-commit hooks** — Ruff, ruff-format, detect-secrets, validaciones de whitespace.
- **Scripts de backup** (`backup_db.ps1`, `restore_db.ps1`) para uso futuro con acceso externo a PostgreSQL.

### Changed
- Arquitectura: mixins unificados en `core/views.py` (`UserOwnedListView`, `UserOwnedCreateView`, etc.).
- Separación de settings en `base.py`, `dev.py`, `prod.py`.

---

## [0.1.0] — 2026-01-15

### Added
- Proyecto inicial Django 5.2 / Python 3.12.
- Autenticación — registro, login, logout, perfil de usuario.
- CRUD de gastos con fecha, descripción, monto y categoría.
- CRUD de ingresos.
- Categorías de sistema predefinidas (`seed_categories`).
- Deploy inicial a Render (Free tier) con PostgreSQL.
- SQLite en desarrollo, PostgreSQL en producción.
