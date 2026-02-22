"""
Vistas para gestión de categorías.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.views import UserFormKwargsMixin

from .forms import CategoryForm
from .models import Category


class CategoryListView(LoginRequiredMixin, ListView):
    """Lista de categorías del usuario."""

    model = Category
    template_name = "categories/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        """Obtiene categorías del sistema y del usuario."""
        return Category.get_user_categories(self.request.user)

    def get_context_data(self, **kwargs):
        """Agrega categorías separadas por tipo al contexto."""
        context = super().get_context_data(**kwargs)

        user = self.request.user
        context["expense_categories"] = Category.get_expense_categories(user)
        context["income_categories"] = Category.get_income_categories(user)

        return context


class CategoryCreateView(LoginRequiredMixin, UserFormKwargsMixin, CreateView):
    """Crear nueva categoría."""

    model = Category
    form_class = CategoryForm
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("categories:list")

    def get_form(self, form_class=None):
        """Asigna el usuario a la instancia antes de validar."""
        form = super().get_form(form_class)
        if not form.instance.pk:  # Solo para nuevas categorías
            form.instance.user = self.request.user
        return form

    def get_context_data(self, **kwargs):
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context

    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(self.request, "Categoría creada correctamente.")
        return response


class CategoryUpdateView(LoginRequiredMixin, UserFormKwargsMixin, UpdateView):
    """Editar categoría existente."""

    model = Category
    form_class = CategoryForm
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("categories:list")

    def get_queryset(self):
        """Solo permite editar categorías propias (no del sistema)."""
        return Category.objects.filter(user=self.request.user, is_system=False)

    def get_context_data(self, **kwargs):
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(self.request, "Categoría actualizada correctamente.")
        return response


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar categoría."""

    model = Category
    template_name = "categories/category_confirm_delete.html"
    success_url = reverse_lazy("categories:list")

    def get_queryset(self):
        """Solo permite eliminar categorías propias (no del sistema)."""
        return Category.objects.filter(user=self.request.user, is_system=False)

    def form_valid(self, form):
        """Elimina la categoría."""
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(self.request, f"Categoría '{self.object.name}' eliminada correctamente.")
        return HttpResponseRedirect(success_url)
