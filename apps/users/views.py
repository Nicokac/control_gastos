"""Vistas de autenticación y perfil de usuario."""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, UpdateView

from apps.core.logging import (
    get_client_ip,
    log_login_attempt,
    log_logout,
    log_password_change,
    log_sensitive_action,
    log_user_registration,
)

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """Vista de login personalizada."""

    authentication_form = LoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("reports:dashboard")

    def form_valid(self, form):
        """Login exitoso."""
        response = super().form_valid(form)

        # Loggear login exitoso
        log_login_attempt(
            username=self.request.user.email, ip_address=get_client_ip(self.request), success=True
        )

        messages.success(self.request, f"¡Bienvenido de vuelta, {form.get_user().username}!")
        return response

    def form_invalid(self, form):
        """Login fallido."""
        # Obtener username del intento fallido
        username = form.cleaned_data.get("username", "unknown")

        log_login_attempt(username=username, ip_address=get_client_ip(self.request), success=False)

        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Vista de logout."""

    next_page = reverse_lazy("users:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Loggear logout antes de cerrar sesión
            log_logout(username=request.user.email, ip_address=get_client_ip(request))
            messages.info(request, "Sesión cerrada correctamente.")
        return super().dispatch(request, *args, **kwargs)


class RegisterView(CreateView):
    """Vista de registro de nuevos usuarios."""

    model = User
    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("reports:dashboard")

    def dispatch(self, request, *args, **kwargs):
        """Redirige si el usuario ya está logueado."""
        if request.user.is_authenticated:
            return redirect("reports:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Loguea al usuario después del registro."""
        response = super().form_valid(form)

        # Loggear registro
        log_user_registration(username=self.object.email, ip_address=get_client_ip(self.request))

        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(
            self.request, f"¡Cuenta creada exitosamente! Bienvenido, {self.object.username}."
        )
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    """Vista para editar perfil de usuario."""

    model = User
    form_class = ProfileForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        """Retorna el usuario actual."""
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Perfil actualizado correctamente.")
        return super().form_valid(form)


class DeleteAccountView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar la cuenta del usuario autenticado."""

    template_name = "users/delete_account.html"
    success_url = reverse_lazy("users:login")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = self.request.user
        log_sensitive_action(
            action="ACCOUNT_DELETED",
            username=user.email,
            ip_address=get_client_ip(self.request),
        )
        logout(self.request)
        user.delete()
        messages.success(self.request, "Tu cuenta fue eliminada correctamente.")
        return redirect(self.success_url)


class BrevoPasswordResetView(PasswordResetView):
    """PasswordResetView que envía el email via Brevo API en lugar de SMTP."""

    template_name = "users/password_reset.html"
    email_template_name = "users/emails/password_reset.txt"
    subject_template_name = "users/emails/password_reset_subject.txt"
    success_url = reverse_lazy("users:password_reset_done")

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        from django.template.loader import render_to_string

        subject = render_to_string(subject_template_name, context).strip()
        body = render_to_string(email_template_name, context)
        brevo_api_key = getattr(settings, "BREVO_API_KEY", "")

        if brevo_api_key:
            try:
                import requests as http_requests

                http_requests.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={"api-key": brevo_api_key, "Content-Type": "application/json"},
                    json={
                        "sender": {"name": "Control Gastos", "email": "kachuknm@gmail.com"},
                        "to": [{"email": to_email}],
                        "subject": subject,
                        "textContent": body,
                    },
                    timeout=10,
                ).raise_for_status()
            except Exception:
                logger.exception("Error al enviar email de reset via Brevo a %s", to_email)
        else:
            super().send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                to_email,
                html_email_template_name,
            )


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Vista para cambiar contraseña."""

    template_name = "users/password_change.html"
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form):
        """Cambio de contraseña exitoso."""
        response = super().form_valid(form)

        # Loggear cambio de contraseña
        log_password_change(
            username=self.request.user.email, ip_address=get_client_ip(self.request)
        )

        messages.success(self.request, "Contraseña actualizada correctamente")
        return response
