"""Vistas de autenticación y perfil de usuario."""

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import CreateView, DeleteView, UpdateView, View

from apps.core.logging import (
    get_client_ip,
    log_login_attempt,
    log_logout,
    log_password_change,
    log_sensitive_action,
    log_user_registration,
)
from apps.core.utils import send_brevo_email

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User
from .tokens import email_verification_token


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse_lazy("users:verify_email", kwargs={"uidb64": uid, "token": token})
    )
    body = (
        f"Hola {user.username},\n\n"
        f"Para verificar tu email hacé clic en el siguiente link:\n\n"
        f"{verify_url}\n\n"
        f"Este link es válido por 7 días.\n\n"
        f"Si no creaste una cuenta, podés ignorar este email.\n\n"
        f"Control de Gastos"
    )
    send_brevo_email(user.email, "Verificá tu email — Control de Gastos", body)


def _send_welcome_email(user):
    body = render_to_string("users/emails/welcome.txt", {"username": user.username})
    send_brevo_email(user.email, "¡Bienvenido a Control de Gastos!", body)


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
        username = form.cleaned_data.get("username", "unknown")
        log_login_attempt(username=username, ip_address=get_client_ip(self.request), success=False)

        from django.conf import settings

        from axes.models import AccessFailureLog

        failure_limit = getattr(settings, "AXES_FAILURE_LIMIT", 5)
        failures = AccessFailureLog.objects.filter(username=username).count()
        remaining = max(0, failure_limit - failures)

        if failures >= 2 and remaining > 0:
            form.errors["__all__"] = form.error_class(
                [
                    f"Credenciales incorrectas. Te quedan {remaining} intento{'s' if remaining != 1 else ''} antes de que se bloquee tu cuenta."
                ]
            )
        elif remaining == 0:
            pass  # Axes ya maneja la redirección al template de bloqueo

        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Vista de logout."""

    next_page = reverse_lazy("users:login")

    def get(self, request, *args, **kwargs):
        return redirect("users:login")

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

        log_user_registration(username=self.object.email, ip_address=get_client_ip(self.request))

        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        _send_verification_email(self.request, self.object)
        messages.success(
            self.request,
            f"¡Cuenta creada exitosamente! Bienvenido, {self.object.username}. "
            "Revisá tu email para verificar tu cuenta.",
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
        subject = render_to_string(subject_template_name, context).strip()
        body = render_to_string(email_template_name, context)

        if not send_brevo_email(to_email, subject, body):
            super().send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                to_email,
                html_email_template_name,
            )


class VerifyEmailView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError):
            user = None

        if user and not user.email_verified and email_verification_token.check_token(user, token):
            user.email_verified = True
            user.save(update_fields=["email_verified"])
            _send_welcome_email(user)
            messages.success(request, "¡Email verificado correctamente!")
        elif user and user.email_verified:
            messages.info(request, "Tu email ya estaba verificado.")
        else:
            messages.error(request, "El link de verificación es inválido o ya expiró.")

        if request.user.is_authenticated:
            return redirect("reports:dashboard")
        return redirect("users:login")


class TourDoneView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.has_seen_tour = True
        request.user.save(update_fields=["has_seen_tour"])
        return JsonResponse({"ok": True})


class TourResetView(LoginRequiredMixin, View):
    def post(self, request):
        request.user.has_seen_tour = False
        request.user.save(update_fields=["has_seen_tour"])
        return redirect("reports:dashboard")


class ResendVerificationView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.email_verified:
            messages.info(request, "Tu email ya está verificado.")
        else:
            _send_verification_email(request, request.user)
            messages.success(request, "Te reenviamos el email de verificación. Revisá tu bandeja.")
        return redirect("reports:dashboard")


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
