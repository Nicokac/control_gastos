"""
Vistas para gestión de categorías.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponseForbidden

from .models import Category
from .forms import CategoryForm
from apps.core.constants import CategoryType

# Create your views here.
class CategoryListView(LoginRequiredMixin, ListView):
    """Lista de categorías del usuario."""

    model = Category
    template_name = 'categories/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        """Obtiene categorías del sistema y del usuario."""
        return Category.get_user_categories(self.request.user)
    
    def get_context_data(self, **kwargs):
        """Agrega categorías separadas por tipo al contexto."""
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        context['expense_categories'] = Category.get_expense_categories(user)
        context['income_categories'] = Category.get_income_categories(user)
        
        return context

class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Crear nueva categoría."""
    
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('categories:list')

    def get_form_kwargs(self):
        """Pasa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Muestra mensaje de éxito."""
        messages.success(self.request, 'Categoría creada correctamente.')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Editar categoría existente."""
    
    model = Category
    form_class = CategoryForm
    template_name = 'categories/category_form.html'
    success_url = reverse_lazy('categories:list')

    def get_queryset(self):
        """Solo permite editar categorías propias (no del sistema)."""
        return Category.objects.filter(
            user=self.request.user,
            is_system=False
        )

    def get_form_kwargs(self):
        """Pasa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Muestra mensaje de éxito."""
        messages.success(self.request, 'Categoría actualizada correctamente.')
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar categoría (soft delete)."""
    
    model = Category
    template_name = 'categories/category_confirm_delete.html'
    success_url = reverse_lazy('categories:list')

    def get_queryset(self):
        """Solo permite eliminar categorías propias (no del sistema)."""
        return Category.objects.filter(
            user=self.request.user,
            is_system=False
        )

    def delete(self, request, *args, **kwargs):
        """Override para usar soft delete."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(request, 'Categoría eliminada correctamente.')
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)
