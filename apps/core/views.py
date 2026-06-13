# Create your views here.
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.core.utils import send_brevo_email

from .forms import FeedbackForm

logger = logging.getLogger(__name__)


class UserOwnedQuerysetMixin(LoginRequiredMixin):
    """Filtra queryset por usuario autenticado."""

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class UserFormKwargsMixin:
    """Pasa user al form via kwargs."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class UserOwnedListView(UserOwnedQuerysetMixin, ListView):
    """ListView base con filtro por usuario y paginación."""

    paginate_by = 20


class UserOwnedCreateView(UserOwnedQuerysetMixin, UserFormKwargsMixin, CreateView):
    """CreateView base que asigna user al objeto."""

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response

    def get_success_message(self):
        return "Registro creado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context


class UserOwnedUpdateView(UserOwnedQuerysetMixin, UserFormKwargsMixin, UpdateView):
    """UpdateView base con filtro por usuario."""

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.get_success_message())
        return response

    def get_success_message(self):
        return "Registro actualizado correctamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context


class UserOwnedDeleteView(UserOwnedQuerysetMixin, DeleteView):
    """DeleteView base con mensaje de éxito."""

    def form_valid(self, form):
        obj = self.get_object()
        success_url = self.get_success_url()
        obj.delete()
        messages.success(self.request, self.get_success_message(obj))
        return HttpResponseRedirect(success_url)

    def get_success_message(self, obj):
        return "Registro eliminado correctamente."


class UserOwnedDetailView(UserOwnedQuerysetMixin, DetailView):
    """DetailView base con filtro por usuario."""

    pass


class FeedbackView(LoginRequiredMixin, FormView):
    """Recibe feedback del usuario y lo envía por email al administrador."""

    template_name = "core/feedback.html"
    form_class = FeedbackForm
    success_url = reverse_lazy("core:feedback")

    TIPO_LABELS = {
        "bug": "Bug / Falla",
        "mejora": "Sugerencia de mejora",
        "pregunta": "Pregunta",
        "otro": "Otro",
    }

    def form_valid(self, form):
        user = self.request.user
        tipo = form.cleaned_data["tipo"]
        mensaje = form.cleaned_data["mensaje"]
        tipo_label = self.TIPO_LABELS.get(tipo, tipo)

        subject = f"[Control de Gastos] {tipo_label} — {user.username}"
        body = f"Usuario: {user.username}\nEmail: {user.email}\nTipo: {tipo_label}\n---\n{mensaje}"
        recipient = getattr(settings, "FEEDBACK_EMAIL", "kachuknm@gmail.com")
        from_email = getattr(
            settings, "DEFAULT_FROM_EMAIL", "Control Gastos <noreply@controlmisfinanzas.com>"
        )
        sent = send_brevo_email(recipient, subject, body)
        if not sent:
            resend_api_key = getattr(settings, "RESEND_API_KEY", "")
            try:
                if resend_api_key:
                    import resend

                    resend.api_key = resend_api_key
                    resend.Emails.send(
                        {"from": from_email, "to": [recipient], "subject": subject, "text": body}
                    )
                else:
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=from_email,
                        recipient_list=[recipient],
                        fail_silently=False,
                    )
                sent = True
            except Exception:
                logger.exception("Error al enviar feedback de usuario %s", user.username)

        if sent:
            messages.success(self.request, "¡Gracias! Tu reporte fue enviado correctamente.")
        else:
            messages.error(
                self.request,
                "No se pudo enviar el reporte. Intentá de nuevo más tarde.",
            )

        return super().form_valid(form)


APP_VERSION = "1.13.5"

WHATS_NEW = [
    {
        "version": "1.12.0",
        "date": "Junio 2026",
        "title": 'Nueva sección "Acerca de"',
        "items": [
            "Conocé la versión de la app, el sitio web y los datos de contacto del desarrollador",
            "Disponible tanto en la versión web (Mi perfil) como en la app móvil (Configuración)",
        ],
    },
    {
        "version": "1.11.0",
        "date": "Junio 2026",
        "title": "App móvil: nueva sección de Ahorros",
        "items": [
            "App móvil: gestioná tus metas de ahorro — creá objetivos, registrá depósitos y retiros, y seguí el progreso con barras visuales",
            "App móvil: cada meta tiene su propio detalle con historial completo de movimientos",
            "App móvil: personalizá cada meta con un ícono y color propios",
            "App móvil: acceso directo a Ahorros desde el dashboard",
        ],
    },
    {
        "version": "1.10.0",
        "date": "Junio 2026",
        "title": "App móvil: Gastos Fijos, Categorías y modo oscuro",
        "items": [
            "App móvil: nueva sección de Gastos Fijos — listá, marcá como pagado, creá y editá tus gastos recurrentes",
            "App móvil: gestión de Categorías directamente desde el celular",
            "App móvil: tema claro, oscuro o automático, con animaciones de transición entre pantallas",
            "App móvil: el dashboard ahora indica cuándo se actualizaron los datos por última vez",
            "App móvil: formularios de gastos e ingresos con mejor diseño — destacan el monto y el color de cada categoría",
        ],
    },
    {
        "version": "1.9.0",
        "date": "Junio 2026",
        "title": "Dashboard y Mi perfil mejorados",
        "items": [
            "Registrá gastos, ingresos y gastos compartidos desde la app",
            "Dashboard con balance del mes, gráfico de categorías y movimientos recientes",
            "Configurá tu perfil, moneda y día de inicio del mes desde la app",
        ],
    },
    {
        "version": "1.8.0",
        "date": "Junio 2026",
        "title": "Categorías y Gastos Fijos mejorados",
        "items": [
            "Gastos Fijos: nuevo campo 'En qué cuota estás' para registrar cuotas ya avanzadas antes de usar la app",
            "Gastos Fijos: el selector de categoría ahora tiene búsqueda en tiempo real — escribí para filtrar",
            "Categorías: elegí cualquier color con el selector libre — paleta rápida o color personalizado con el picker del browser",
            "Categorías: vista previa en tiempo real del ícono, color y nombre mientras editás",
            "Categorías: los íconos de la lista ahora muestran el color asignado a cada categoría",
            "Categorías: al intentar eliminar un grupo con subcategorías, la app lo avisa claramente antes de confirmar",
        ],
    },
    {
        "version": "1.7.1",
        "date": "Junio 2026",
        "title": "Tour inicial mejorado",
        "items": [
            "Tour de bienvenida ampliado: ahora incluye los pasos de Ingresos y Gastos Fijos",
            "Textos del tour actualizados con más detalle sobre cada sección",
            "Podés volver a ver el tour desde Mi cuenta en cualquier momento",
        ],
    },
    {
        "version": "1.7.0",
        "date": "Junio 2026",
        "title": "Reportes — resumen mensual y reporte anual",
        "items": [
            "Dashboard: nuevo botón 'Excel' que descarga el resumen del mes — balance, gastos por categoría e ingresos por categoría",
            "Nuevo Reporte Anual: tabla comparativa con los 12 meses del año — ingresos, gastos, ahorro y balance de cada mes",
            "Reporte Anual: hacé click en cualquier mes para ver el detalle en el dashboard",
            "Reporte Anual: exportable a Excel con colores por balance positivo/negativo",
        ],
    },
    {
        "version": "1.6.0",
        "date": "Junio 2026",
        "title": "Gastos Compartidos del hogar",
        "items": [
            "Nueva sección 'Gastos Compartidos' — registrá quién pagó qué en el hogar y llevá el control mes a mes",
            "Tabla estilo planilla con columnas por persona: ves de un vistazo cuánto gastó cada uno y en qué categoría",
            "Panel de resumen con el total de cada persona en el período",
            "Exportación a Excel (.xlsx) con grupos, subtotales y totales por persona",
            "Agregá los miembros de tu hogar desde la sección de Miembros",
        ],
    },
    {
        "version": "1.5.2",
        "date": "Junio 2026",
        "title": "Landing renovada y resumen con memoria",
        "items": [
            "Gastos e Ingresos: el panel 'Ver resumen' recuerda si lo dejaste abierto o cerrado — no tenés que volver a abrirlo cada vez",
            "Landing: nueva sección con screenshots reales de la app — mirá el dashboard, gastos, ahorros y gastos fijos antes de registrarte",
            "Landing: hacé click en cualquier screenshot para verlo a pantalla completa",
        ],
    },
    {
        "version": "1.5.1",
        "date": "Mayo 2026",
        "title": "Gastos: más gráficos en el resumen",
        "items": [
            "Gastos: gráfico de barras con el gasto de cada día del mes — hacé click en una barra para ver los gastos de ese día",
            "Gastos: donuts de distribución por tipo de gasto y por método de pago en el panel 'Ver resumen'",
        ],
    },
    {
        "version": "1.5.0",
        "date": "Mayo 2026",
        "title": "Período financiero personalizado",
        "items": [
            "Mi cuenta: configurá el día en que empieza tu mes financiero — ideal si cobrás el sueldo a mediados de mes",
            "Dashboard: los totales de gastos e ingresos reflejan tu período financiero real, no el mes calendario",
            "El texto 'Día X de Y' es clickeable y lleva directamente a la configuración",
        ],
    },
    {
        "version": "1.4.9",
        "date": "Mayo 2026",
        "title": "Alerta de presupuesto y cotización USD inteligente",
        "items": [
            "Dashboard: alerta visual cuando tus gastos superan el umbral configurado — la barra cambia a rojo y aparece un aviso",
            "Mi cuenta: nuevo campo 'Umbral de alerta (%)' — configurá a partir de qué porcentaje querés recibir la alerta",
            "Formulario de gastos e ingresos: al seleccionar USD, el campo cotización se pre-completa con el último valor que usaste",
        ],
    },
    {
        "version": "1.4.8",
        "date": "Mayo 2026",
        "title": "Ingresos Fijos: nuevo módulo para ingresos recurrentes",
        "items": [
            "Nueva sección 'Ingresos Fijos' en el menú — modelá tu sueldo, alquiler cobrado o cualquier ingreso que se repite cada mes",
            "Registrá el cobro con un click — el formulario se pre-completa con la categoría y descripción del ingreso fijo",
            "Estado del mes: verde cuando está cobrado, amarillo cuando está pendiente",
            "Los ingresos fijos inactivos se ocultan por defecto para mantener la lista limpia",
        ],
    },
    {
        "version": "1.4.7",
        "date": "Mayo 2026",
        "title": "Gastos Fijos: cuotas y organización de inactivos",
        "items": [
            "Gastos Fijos: podés indicar que un gasto es en cuotas — al pagar la última, se desactiva automáticamente",
            "Gastos Fijos: el badge muestra el progreso de cuotas (ej: 'cuota 3/12') directamente en la lista",
            "Gastos Fijos: los gastos inactivos se ocultan por defecto — usá el botón 'Mostrar inactivos' para verlos",
        ],
    },
    {
        "version": "1.4.6",
        "date": "Mayo 2026",
        "title": "Gastos: gráfico de acumulado diario del mes",
        "items": [
            "Gastos: el panel 'Ver resumen' ahora incluye un gráfico de línea con el gasto acumulado día a día dentro del mes filtrado",
            "El gráfico se oculta automáticamente cuando el filtro es solo por año — sin mes específico",
            "Los JS de la app ahora incluyen versión en la URL para evitar problemas de caché al actualizar",
        ],
    },
    {
        "version": "1.4.5",
        "date": "Mayo 2026",
        "title": "Gastos: gráfico de distribución por grupo",
        "items": [
            "Gastos: el panel 'Ver resumen' ahora incluye un donut chart con la distribución del período por grupo de categoría",
            "Gastos: la leyenda muestra cada grupo con su color, porcentaje y barra de ranking — hacé click para filtrar la tabla a ese grupo",
            "Gastos: los segmentos pequeños (menos del 3%) se agrupan automáticamente en 'Otros' para mantener el gráfico legible",
            "Gastos: tipo de gasto y método de pago ahora muestran porcentajes y barras de progreso en el resumen",
        ],
    },
    {
        "version": "1.4.4",
        "date": "Mayo 2026",
        "title": "Ingresos: paridad completa con Gastos",
        "items": [
            "Ingresos: el resumen del período ahora incluye desglose por categoría con el botón 'Ver resumen'",
            "Ingresos: nuevos filtros de monto mínimo y máximo para encontrar ingresos en un rango específico",
        ],
    },
    {
        "version": "1.4.3",
        "date": "Mayo 2026",
        "title": "Mejoras en la lista y formulario de Gastos",
        "items": [
            "Gastos: el resumen del período ahora incluye desglose por categoría individual, además de tipo y método de pago",
            "Gastos: nuevos filtros de monto mínimo y máximo para encontrar gastos grandes o en un rango específico",
            "Gastos: método de pago y tipo de gasto ahora están siempre visibles en el formulario, sin necesidad de expandir",
            "Gastos: la vista de detalle muestra siempre método de pago y tipo, con link para completarlos si están vacíos",
        ],
    },
    {
        "version": "1.4.2",
        "date": "Mayo 2026",
        "title": "Dashboard: acciones en transacciones y gráfico navegable",
        "items": [
            "Dashboard: las últimas transacciones tienen botones de editar y eliminar directamente en la lista, sin salir del dashboard",
            "Dashboard: el gráfico de evolución mensual es clickeable — hacé click en cualquier punto para ver el dashboard de ese mes",
            "Dashboard: links directos a la lista de gastos e ingresos del período desde la sección de últimas transacciones",
        ],
    },
    {
        "version": "1.4.1",
        "date": "Mayo 2026",
        "title": "Búsqueda en categorías y ordenamiento de listas",
        "items": [
            "Gastos e Ingresos: hacé click en los encabezados Fecha, Categoría, Descripción o Monto para ordenar la lista — un segundo click invierte el orden",
            "Formulario de Gasto e Ingreso: buscá tu categoría escribiendo en el campo de búsqueda — los grupos sin coincidencias se ocultan automáticamente",
        ],
    },
    {
        "version": "1.4.0",
        "date": "Mayo 2026",
        "title": "Mejoras en Categorías",
        "items": [
            "Categorías: búsqueda en tiempo real dentro de cada sección — filtrá grupos y subcategorías de Gastos e Ingresos de forma independiente",
            "Categorías: botón × para limpiar el campo de búsqueda en un click",
            "Categorías: los grupos de sistema se simplificaron — ahora solo existe 'Sin clasificar' en Gastos y 'Sueldo' en Ingresos, ambos con la opción de agregar subcategorías propias",
        ],
    },
    {
        "version": "1.3.0",
        "date": "Mayo 2026",
        "title": "Dashboard mejorado y paridad Gastos/Ingresos",
        "items": [
            "Dashboard: navegación por período — usá las flechas para ver cualquier mes anterior sin perder el contexto",
            "Dashboard: nueva card de Ahorro junto a Gastos e Ingresos, con progreso global hacia tus metas activas",
            "Dashboard: las cards de Gastos e Ingresos son clickeables y llevan directo a la lista del período",
            "Dashboard: los gastos fijos pendientes se muestran como badges debajo de la barra de progreso",
            "Dashboard: la barra de balance muestra el día del mes y cuánto te queda disponible",
            "Gastos: buscá por nombre de categoría o grupo además de por descripción",
            "Gastos: botón duplicar para copiar un gasto existente con todos sus datos precargados",
            "Gastos: método de pago y tipo siempre visibles en los filtros, sin necesidad de expandir",
            "Gastos: el estado vacío diferencia entre 'sin datos' y 'sin resultados para los filtros aplicados'",
            "Ingresos: paridad con la sección de Gastos — duplicar, modal de eliminación, búsqueda por categoría y estado vacío diferenciado",
            "General: botón 'Volver' contextual en todas las listas — aparece solo cuando hay una página anterior en el mismo sitio",
            "General: mensajes de error de validación unificados en todos los formularios",
        ],
    },
    {
        "version": "1.2.1",
        "date": "Mayo 2026",
        "title": "Correcciones de interfaz",
        "items": [
            "Dashboard: el ícono del widget de Gastos ahora representa correctamente un egreso",
            "Dashboard: cuando no hay ingresos registrados en el mes, ya no muestra '0% de tus ingresos' — en cambio aparece un mensaje explicativo",
            "Dashboard: las últimas transacciones ahora muestran el ícono y nombre de categoría de cada movimiento",
            "General: el botón + ahora lleva a crear el tipo correcto según la sección — en Ingresos crea un ingreso, en Ahorro una meta, etc.",
            "General: al intentar guardar un gasto o ingreso sin categoría, aparece un mensaje de error claro debajo del selector",
            "General: el botón Cancelar tiene el mismo estilo en todos los formularios",
            "General: las fechas ahora se muestran siempre en español, incluyendo Gastos Fijos y Mi Perfil",
            "General: el toast de confirmación ya no mostraba el carácter guion como código unicode",
        ],
    },
    {
        "version": "1.2.0",
        "date": "Mayo 2026",
        "title": "Formulario de categorías más inteligente",
        "items": [
            "Categorías: al elegir Gasto o Ingreso en el formulario, el selector de grupo padre filtra automáticamente y muestra solo los grupos del mismo tipo",
            "Categorías: ya no es posible crear una categoría con el mismo nombre que una categoría del sistema",
            "Categorías: los grupos del sistema ya no muestran la opción de agregar subcategorías, eliminando una inconsistencia visual",
        ],
    },
    {
        "version": "1.1.1",
        "date": "Mayo 2026",
        "title": "Mejoras en Categorías",
        "items": [
            "Categorías: el botón de nuevo gasto rápido ya no aparece en la pantalla de categorías para evitar confusión",
            "Categorías: cada grupo ahora muestra la cantidad de subcategorías entre paréntesis",
        ],
    },
    {
        "version": "1.1.0",
        "date": "Mayo 2026",
        "title": "Mejoras de usabilidad y correcciones",
        "items": [
            "Montos: los campos de monto ahora muestran coma decimal y punto de miles al estilo argentino (ej: 1.234,50) en todos los formularios",
            "Novedades: el historial de versiones anteriores a v1.0 se agrupa en un desplegable para no sobrecargar la pantalla",
            "General: cerrar sesión desde un link directo redirige al login en lugar de mostrar un error 403",
        ],
    },
    {
        "version": "1.0.0",
        "date": "Mayo 2026",
        "title": "Lanzamiento v1.0",
        "items": [
            "Primera versión estable de Control de Gastos",
            "Incluye dashboard, gastos, ingresos, ahorro, categorías, gastos fijos,  y verificación de email",
        ],
    },
    {
        "version": "0.32.0",
        "date": "Mayo 2026",
        "title": "Tour interactivo",
        "items": [
            "Al entrar por primera vez al dashboard se activa un tour que muestra las secciones principales de la app",
            "Podés volver a ver el tour desde Mi Perfil en cualquier momento",
        ],
    },
    {
        "version": "0.31.0",
        "date": "Mayo 2026",
        "title": "Smoke tests y SLA documentado",
        "items": [
            "Infraestructura: cada push a main verifica automáticamente que los endpoints de producción responden correctamente",
        ],
    },
    {
        "version": "0.30.0",
        "date": "Mayo 2026",
        "title": "Email de bienvenida",
        "items": [
            "Al verificar tu email recibís un mensaje de bienvenida con tips para arrancar a usar la app",
        ],
    },
    {
        "version": "0.29.0",
        "date": "Mayo 2026",
        "title": "Infraestructura y docs",
        "items": [
            "General: configuración de Render versionada en el repositorio (`render.yaml`)",
        ],
    },
    {
        "version": "0.28.0",
        "date": "Mayo 2026",
        "title": "Confirmación de email",
        "items": [
            "Seguridad: al registrarte recibirás un email para verificar tu cuenta",
            "Un banner te avisa si tu email aún no fue verificado, con opción de reenviar el link",
        ],
    },
    {
        "version": "0.27.0",
        "date": "Mayo 2026",
        "title": "Backup automático de base de datos",
        "items": [
            "General: la base de datos se respalda automáticamente cada día a Cloudflare R2 — tus datos están protegidos",
        ],
    },
    {
        "version": "0.26.0",
        "date": "Mayo 2026",
        "title": "Términos, privacidad y registro mejorado",
        "items": [
            "Nuevas páginas de Términos y condiciones y Política de privacidad accesibles desde el footer",
            "Registro: ahora se requiere aceptar los términos antes de crear una cuenta",
        ],
    },
    {
        "version": "0.25.0",
        "date": "Mayo 2026",
        "title": "Recuperar contraseña",
        "items": [
            "Login: nuevo link '¿Olvidaste tu contraseña?' para resetear la contraseña por email",
            "General: los emails de la app ahora se envían via Brevo (antes Resend requería dominio propio)",
        ],
    },
    {
        "version": "0.24.0",
        "date": "Mayo 2026",
        "title": "Mejoras en Gastos Fijos",
        "items": [
            "Dashboard: nuevo widget que muestra cuántos gastos fijos fueron pagados este mes, con indicador de vencidos",
            "Gastos Fijos: los íconos de estado ahora muestran un tooltip al pasar el mouse con la descripción del estado",
        ],
    },
    {
        "version": "0.23.0",
        "date": "Mayo 2026",
        "title": "Gastos Fijos",
        "items": [
            "Nueva sección Gastos Fijos para registrar servicios, impuestos y cuotas mensuales",
            "Seguimiento del estado de cada gasto fijo: pagado, pendiente o vencido",
            "Registrar un pago desde la lista pre-completa el formulario con la categoría y descripción del gasto fijo",
            "Resumen del mes: cuántos gastos fijos ya fueron pagados sobre el total activo",
        ],
    },
    {
        "version": "0.22.0",
        "date": "Mayo 2026",
        "title": "Exportar Gastos e Ingresos a CSV",
        "items": [
            "Gastos: nuevo botón para descargar los gastos del período actual como archivo CSV, respetando los filtros aplicados",
            "Ingresos: nuevo botón para descargar los ingresos del período actual como archivo CSV, respetando los filtros aplicados",
        ],
    },
    {
        "version": "0.21.0",
        "date": "Mayo 2026",
        "title": "Reordenamiento de grupos de categorías",
        "items": [
            "Categorías: ahora podés arrastrar los grupos para cambiar el orden en que aparecen en la lista",
        ],
    },
    {
        "version": "0.20.0",
        "date": "Mayo 2026",
        "title": "Mejoras en Gastos y Categorías",
        "items": [
            "Gastos: la tabla ahora muestra la categoría antes que la descripción, para encontrar los gastos más fácil",
            "Categorías: los grupos ahora se pueden contraer y expandir haciendo clic en el encabezado — el estado se recuerda entre visitas",
        ],
    },
    {
        "version": "0.19.0",
        "date": "Mayo 2026",
        "title": "Búsqueda por texto en Gastos e Ingresos",
        "items": [
            "Gastos: nuevo campo de búsqueda en los filtros para encontrar transacciones por descripción",
            "Ingresos: nuevo campo de búsqueda en los filtros para encontrar transacciones por descripción",
        ],
    },
    {
        "version": "0.16.0",
        "date": "Mayo 2026",
        "title": "Comparar evolución por año",
        "items": [
            "Dashboard: ahora podés ver la evolución de cualquier año anterior usando el selector en el gráfico",
        ],
    },
    {
        "version": "0.15.0",
        "date": "Mayo 2026",
        "title": "Mejoras en Novedades y Reportar / Sugerir",
        "items": [
            'Novedades: el aviso de "Nuevo" en el menú ahora se actualiza automáticamente con cada versión',
            "Novedades: cada cambio ahora indica en qué sección de la app ocurrió",
        ],
    },
    {
        "version": "0.14.0",
        "date": "Mayo 2026",
        "title": "Correcciones en Reportar / Sugerir",
        "items": [
            "Reportar / Sugerir: ahora aparece un mensaje de confirmación cuando tu reporte se envía correctamente",
            "Reportar / Sugerir: el mensaje de error desaparece automáticamente cuando empezás a escribir",
            'Reportar / Sugerir: el botón ya no muestra "Procesando..." si el campo está vacío',
        ],
    },
    {
        "version": "0.13.0",
        "date": "Mayo 2026",
        "title": "Mejoras en Mi Cuenta",
        "items": [
            "Mi Cuenta: nueva opción para eliminar tu cuenta y todos tus datos de forma permanente",
            "Mi Cuenta: la fecha y hora del último acceso ahora se muestra en horario argentino",
        ],
    },
    {
        "version": "0.12.0",
        "date": "Mayo 2026",
        "title": "Mejoras en Categorías y Mi Cuenta",
        "items": [
            "Categorías: el selector de color ahora muestra círculos de colores en lugar del selector del sistema",
            "Mi Cuenta: el nombre y apellido ahora se muestran correctamente al abrir el formulario",
        ],
    },
    {
        "version": "0.11.0",
        "date": "Mayo 2026",
        "title": "Correcciones en Ingresos y Ahorro",
        "items": [
            "Ingresos: el total del período ahora muestra el monto correcto",
            "Ingresos: las categorías ahora aparecen correctamente al registrar un ingreso",
            "Ahorro: el monto objetivo y el color ahora se muestran correctamente al editar una meta",
        ],
    },
    {
        "version": "0.10.0",
        "date": "Mayo 2026",
        "title": "Correcciones en Gastos",
        "items": [
            "Gastos: el monto ya no aparece vacío al editar un gasto existente",
            "Gastos: el resumen ahora incluye los gastos sin tipo o método de pago asignado",
        ],
    },
    {
        "version": "0.9.0",
        "date": "Mayo 2026",
        "title": "Menú en celular y sección Novedades",
        "items": [
            "El menú lateral ahora está disponible en celular como un panel deslizable",
            "Nueva sección Novedades para ver qué cambió en cada versión de la app",
        ],
    },
    {
        "version": "0.8.0",
        "date": "Mayo 2026",
        "title": "Menú lateral contraíble",
        "items": [
            "El menú lateral ahora se puede reducir a solo íconos para ganar espacio en pantalla",
            "La app recuerda si lo dejaste abierto o cerrado entre sesiones",
        ],
    },
    {
        "version": "0.7.0",
        "date": "Mayo 2026",
        "title": "Correcciones generales",
        "items": [
            "Reportar / Sugerir: el formulario de contacto ahora funciona correctamente",
            "General: el cambio de día ahora ocurre a medianoche en horario argentino",
        ],
    },
    {
        "version": "0.6.0",
        "date": "Mayo 2026",
        "title": "Categorías organizadas en grupos",
        "items": [
            "Categorías: ahora se organizan en grupos (ej: Alimentación) y subcategorías (ej: Supermercado)",
            "Gastos: nuevo filtro por grupo y subcategoría en el listado",
            "Dashboard: podés ver el detalle de gastos por subcategoría desde el ranking",
        ],
    },
    {
        "version": "0.5.0",
        "date": "Mayo 2026",
        "title": "Dashboard rediseñado y nuevas funciones",
        "items": [
            "Dashboard: nuevo gráfico de evolución mensual con ingresos, gastos, ahorro y balance",
            "Dashboard: balance principal destacado, gráfico de categorías y ranking de gastos",
            "Gastos: podés vincular un gasto a una meta de ahorro para que el monto se deposite automáticamente",
            "Categorías y Ahorro: selector visual de íconos para personalizar cada elemento",
            "Nueva sección Reportar / Sugerir disponible en el menú lateral",
        ],
    },
]


class WhatsNewView(LoginRequiredMixin, TemplateView):
    template_name = "core/whats_new.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stable"] = [r for r in WHATS_NEW if not r["version"].startswith("0.")]
        context["prelaunch"] = [r for r in WHATS_NEW if r["version"].startswith("0.")]
        context["app_version"] = APP_VERSION
        return context


class TermsView(TemplateView):
    template_name = "core/terms.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


class LandingView(TemplateView):
    template_name = "core/landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            from django.shortcuts import redirect

            return redirect("reports:dashboard")
        return super().dispatch(request, *args, **kwargs)
