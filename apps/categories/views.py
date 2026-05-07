"""
Vistas para gestión de categorías.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
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
        return (
            Category.objects.filter(models.Q(is_system=True) | models.Q(user=self.request.user))
            .select_related("parent")
            .order_by("type", "parent__name", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from apps.core.constants import CategoryType

        context["expense_tree"] = self._build_full_tree(user, CategoryType.EXPENSE)
        context["income_tree"] = self._build_full_tree(user, CategoryType.INCOME)
        return context

    @staticmethod
    def _build_full_tree(user, category_type):
        """
        Retorna lista de {group, subcategories} incluyendo grupos sin subcategorías.
        Los grupos del sistema sin subs se omiten; los del usuario siempre se incluyen.
        """
        tree = Category.get_categories_by_group(user, category_type)
        tree_group_pks = {entry["group"].pk for entry in tree}

        all_groups = Category.get_groups(user, category_type)
        for group in all_groups:
            if group.pk not in tree_group_pks and not group.is_system:
                tree.append({"group": group, "subcategories": []})

        return sorted(tree, key=lambda e: e["group"].name)


class CategoryCreateView(LoginRequiredMixin, UserFormKwargsMixin, CreateView):
    """Crear nueva categoría."""

    model = Category
    form_class = CategoryForm
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("categories:list")

    def _get_preset_parent(self):
        """Retorna el grupo pre-seleccionado desde ?parent=<pk>, validando que sea accesible."""
        pk = self.request.GET.get("parent")
        if pk:
            try:
                return Category.objects.get(
                    pk=pk,
                    parent__isnull=True,  # solo grupos
                )
            except (Category.DoesNotExist, ValueError):
                pass
        return None

    def get_initial(self):
        initial = super().get_initial()
        parent = self._get_preset_parent()
        if parent:
            initial["parent"] = parent
            initial["type"] = parent.type
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not form.instance.pk:
            form.instance.user = self.request.user
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        context["preset_parent"] = self._get_preset_parent()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Categoría creada correctamente.")
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar la categoría. Revisá los campos marcados. Nombre y tipo son obligatorios.",
        )
        return super().form_invalid(form)


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
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        context["is_subcategory"] = self.object.is_subcategory
        return context

    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(self.request, "Categoría actualizada correctamente.")
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar la categoría. Revisá los campos marcados.",
        )
        return super().form_invalid(form)


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
