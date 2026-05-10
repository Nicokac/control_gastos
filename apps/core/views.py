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
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "onboarding@resend.dev")
        resend_api_key = getattr(settings, "RESEND_API_KEY", "")

        try:
            if resend_api_key:
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


APP_VERSION = "0.12.0"

WHATS_NEW = [
    {
        "version": "0.12.0",
        "date": "Mayo 2026",
        "title": "Mejoras en Categorías",
        "items": [
            "Selector de color visual con círculos predefinidos (ya no se usa el selector nativo del sistema operativo)",
        ],
    },
    {
        "version": "0.11.0",
        "date": "Mayo 2026",
        "title": "Correcciones en Ingresos y Ahorro",
        "items": [
            "Ingresos: el total del período ya muestra el monto correcto",
            "Ingresos: las categorías ahora se cargan correctamente en los formularios",
            "Ahorro: el monto objetivo y el color se pre-cargan al editar una meta",
        ],
    },
    {
        "version": "0.10.0",
        "date": "Mayo 2026",
        "title": "Correcciones en gastos",
        "items": [
            "El monto ya no aparece vacío al editar un gasto existente",
            'El resumen de gastos ahora muestra "Sin clasificar" para los que no tienen tipo o método de pago',
        ],
    },
    {
        "version": "0.9.0",
        "date": "Mayo 2026",
        "title": "Sidebar mobile y mejoras de navegación",
        "items": [
            "Sidebar disponible en celular como menú deslizable",
            "Sección Novedades para seguir la evolución de la app",
        ],
    },
    {
        "version": "0.8.0",
        "date": "Mayo 2026",
        "title": "Sidebar colapsable",
        "items": [
            "El sidebar ahora se puede contraer a solo íconos para ganar espacio",
            "El estado se recuerda entre sesiones",
            "Corrección del layout horizontal en todas las pantallas",
        ],
    },
    {
        "version": "0.7.0",
        "date": "Mayo 2026",
        "title": "Correcciones de producción",
        "items": [
            "Formulario de feedback ahora funciona correctamente en producción",
            "El cambio de día a las 21hs (hora Argentina) quedó corregido",
        ],
    },
    {
        "version": "0.6.0",
        "date": "Mayo 2026",
        "title": "Jerarquía de categorías",
        "items": [
            "Las categorías ahora se organizan en grupos y subcategorías",
            "Filtro por grupo y subcategoría en la lista de gastos",
            "Dashboard con drill-down por subcategoría en el ranking",
        ],
    },
    {
        "version": "0.5.0",
        "date": "Mayo 2026",
        "title": "Dashboard rediseñado y nuevas funciones",
        "items": [
            "Nuevo gráfico de evolución mensual (ingresos, gastos, ahorro, balance)",
            "Dashboard con balance hero, donut de categorías y ranking",
            "Formulario de feedback desde el sidebar",
            "Selector visual de íconos en categorías y metas",
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
