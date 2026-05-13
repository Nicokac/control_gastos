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
        brevo_api_key = getattr(settings, "BREVO_API_KEY", "")
        resend_api_key = getattr(settings, "RESEND_API_KEY", "")

        try:
            if brevo_api_key:
                import requests as http_requests

                http_requests.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={
                        "api-key": brevo_api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "sender": {"name": "Control Gastos", "email": "kachuknm@gmail.com"},
                        "to": [{"email": recipient}],
                        "subject": subject,
                        "textContent": body,
                    },
                    timeout=10,
                ).raise_for_status()
            elif resend_api_key:
                import resend

                resend.api_key = resend_api_key
                resend.Emails.send(
                    {
                        "from": from_email,
                        "to": [recipient],
                        "subject": subject,
                        "text": body,
                    }
                )
            else:
                send_mail(
                    subject=subject,
                    message=body,
                    from_email=from_email,
                    recipient_list=[recipient],
                    fail_silently=False,
                )
            messages.success(self.request, "¡Gracias! Tu reporte fue enviado correctamente.")
        except Exception:
            logger.exception("Error al enviar feedback de usuario %s", user.username)
            messages.error(
                self.request,
                "No se pudo enviar el reporte. Intentá de nuevo más tarde.",
            )

        return super().form_valid(form)


APP_VERSION = "0.27.0"

WHATS_NEW = [
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
        context["whats_new"] = WHATS_NEW
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
