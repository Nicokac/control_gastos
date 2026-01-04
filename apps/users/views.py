"""Vistas de autenticación y perfil de usuario."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from apps.core.logging import (
    get_client_ip,
    log_login_attempt,
    log_logout,
    log_password_change,
    log_user_registration,
)

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import User


class CustomLoginView(LoginView):
    """Vista de login personalizada."""

    authentication_form = LoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("categories:list")

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
