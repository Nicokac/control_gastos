"""Vistas de autenticación y perfil de usuario."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import LoginForm, RegisterForm, ProfileForm
from .models import User


# Create your views here.
class CustomLoginView(LoginView):
    """Vista de login personalizada."""

    form_class = LoginForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('categories:list')
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'¡Bienvenido de vuelta, {form.get_user().username}!'
        )
        return super().form_valid(form)
    

class CustomLogoutView(LogoutView):
    """Vista de logout."""

    next_page = reverse_lazy('users:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Sesión cerrada correctamente.')
        return super().dispatch(request, *args, **kwargs)
    

class RegisterView(CreateView):
    """Vista de registro de nuevos usuarios."""

    model = User
    form_class = RegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('reports:dashboard')

    def dispatch(self, request, *args, **kwargs):
        """Redirige si el usuario ya está logueado."""
        if request.user.is_authenticated:
            return redirect('reports:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Loguea al usuario después del registro."""
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f'¡Cuenta creada exitosamente! Bienvenido, {self.object.username}.'
        )
        return response
    
class ProfileView(LoginRequiredMixin, UpdateView):
    """Vista para editar perfil de usuario."""

    model = User
    form_class = ProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        """Retorna el usuario actual."""
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Perfil actualizado correctamente.')
        return super().form_valid(form)
    
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Vista para cambiar contraseña."""

    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Contraseña actualizada correctamente')
        return super().form_valid(form)
