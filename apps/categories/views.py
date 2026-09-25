"""
Vistas para gestión de categorías.
"""

import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.constants import CATEGORY_COLOR_CHOICES
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
            if group.pk not in tree_group_pks:
                tree.append({"group": group, "subcategories": []})

        return sorted(tree, key=lambda e: (e["group"].order, e["group"].name))


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
        context["color_palette"] = CATEGORY_COLOR_CHOICES
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
        context["color_palette"] = CATEGORY_COLOR_CHOICES
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["children"] = list(Category.objects.filter(parent=self.object).order_by("name"))
        return context

    def form_valid(self, form):
        """Elimina la categoría, bloqueando si tiene referencias protegidas."""
        self.object = self.get_object()
        try:
            self.object.delete()
        except ProtectedError:
            if self.object.is_group:
                msg = (
                    f"No podés eliminar '{self.object.name}' porque tiene subcategorías. "
                    "Eliminá o mové las subcategorías primero."
                )
            else:
                msg = (
                    f"No podés eliminar '{self.object.name}' porque tiene gastos, ingresos "
                    "u otros registros asociados."
                )
            messages.error(self.request, msg)
            return HttpResponseRedirect(self.get_success_url())
        messages.success(self.request, f"Categoría '{self.object.name}' eliminada correctamente.")
        return HttpResponseRedirect(self.get_success_url())


class CategoryQuickCreateView(LoginRequiredMixin, View):
    """Crea una subcategoría de gasto vía AJAX desde el import de PDF.
    Si parent_pk es "new", primero crea el grupo (new_group_name) y la subcategoría debajo."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Datos inválidos."}, status=400)

        from apps.core.constants import CATEGORY_COLOR_CHOICES, CategoryType

        parent_pk = data.get("parent_pk")
        name = (data.get("name") or "").strip()

        if not parent_pk or not name:
            return JsonResponse({"error": "Nombre y grupo son obligatorios."}, status=400)

        if parent_pk == "new":
            new_group_name = (data.get("new_group_name") or "").strip()
            if not new_group_name:
                return JsonResponse({"error": "El nombre del grupo es obligatorio."}, status=400)

            parent = Category(
                name=new_group_name,
                type=CategoryType.EXPENSE,
                user=request.user,
                parent=None,
                color=CATEGORY_COLOR_CHOICES[0][0],
            )
            try:
                parent.full_clean()
                parent.save()
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)
        else:
            try:
                parent = Category.objects.get(
                    models.Q(is_system=True) | models.Q(user=request.user),
                    pk=parent_pk,
                    parent__isnull=True,
                )
            except (Category.DoesNotExist, ValueError):
                return JsonResponse({"error": "Grupo no encontrado."}, status=404)

        new_cat = Category(
            name=name,
            type=CategoryType.EXPENSE,
            user=request.user,
            parent=parent,
            color=parent.color,
            icon=parent.icon,
        )
        try:
            new_cat.full_clean()
            new_cat.save()
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse(
            {
                "pk": new_cat.pk,
                "name": new_cat.name,
                "parent_pk": parent.pk,
                "parent_name": parent.name,
                "label": f"{parent.name} › {new_cat.name}",
            }
        )


class CategoryReorderView(LoginRequiredMixin, View):
    """Recibe lista ordenada de IDs de grupos y actualiza su campo order."""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            ordered_ids = data.get("ids", [])
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Datos inválidos."}, status=400)

        if not isinstance(ordered_ids, list):
            return JsonResponse({"error": "Se esperaba una lista de IDs."}, status=400)

        groups = Category.objects.filter(
            pk__in=ordered_ids,
            user=request.user,
            parent__isnull=True,
        )
        group_map = {g.pk: g for g in groups}

        to_update = []
        for position, pk in enumerate(ordered_ids):
            group = group_map.get(pk)
            if group:
                group.order = position
                to_update.append(group)

        Category.objects.bulk_update(to_update, ["order"])
        return JsonResponse({"ok": True})
