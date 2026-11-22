from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.v1.pagination import ConfigurablePageNumberPagination
from apps.api.v1.serializers.categories import CategoryRuleSerializer, CategorySerializer
from apps.categories.forms import CategoryLimitForm
from apps.categories.models import Category, CategoryOverride, CategoryRule
from apps.core.constants import CategoryType


class CategoryRuleViewSet(viewsets.ModelViewSet):
    """Reglas de categorización del usuario (la pantalla Reglas de la web)."""

    permission_classes = [IsAuthenticated]
    serializer_class = CategoryRuleSerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CategoryRule.objects.none()
        return (
            CategoryRule.objects.filter(user=self.request.user)
            .select_related("category__parent")
            .order_by("pattern")
        )


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Category.objects.none()

        from django.db import models as db_models

        qs = (
            Category.objects.filter(
                db_models.Q(is_system=True) | db_models.Q(user=self.request.user)
            )
            .select_related("parent")
            .order_by("type", "parent__name", "name")
        )
        category_type = self.request.query_params.get("type")
        if category_type in (CategoryType.EXPENSE, CategoryType.INCOME):
            qs = qs.filter(type=category_type)
        parent = self.request.query_params.get("parent")
        if parent == "null":
            qs = qs.filter(parent__isnull=True)
        elif parent:
            qs = qs.filter(parent__pk=parent)
        return qs

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "request": self.request}

    def _check_not_system(self, instance):
        if instance.is_system:
            raise PermissionDenied("No podés modificar categorías del sistema.")
        if instance.user != self.request.user:
            raise PermissionDenied("No tenés permiso para modificar esta categoría.")

    def update(self, request, *args, **kwargs):
        self._check_not_system(self.get_object())
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._check_not_system(self.get_object())
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="hide")
    def hide(self, request, pk=None):
        """Oculta una categoría de sistema de los selectores de este usuario,
        sin afectar a otros usuarios ni a transacciones ya cargadas (DT-086)."""
        category = self.get_object()
        if not category.is_system:
            raise PermissionDenied("Solo se pueden ocultar categorías del sistema.")
        CategoryOverride.objects.update_or_create(
            user=request.user, category=category, defaults={"is_hidden": True}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="unhide")
    def unhide(self, request, pk=None):
        """Revierte el ocultamiento de una categoría de sistema (DT-086)."""
        category = self.get_object()
        # Se actualiza en vez de borrar para no perder el límite mensual (DT-120).
        CategoryOverride.objects.filter(user=request.user, category=category).update(
            is_hidden=False
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="limit")
    def limit(self, request, pk=None):
        """Límite mensual propio en una subcategoría de gasto del sistema (DT-120)."""
        category = self.get_object()
        if not category.is_system:
            raise PermissionDenied("Las categorías propias se editan directamente.")
        override = CategoryOverride.objects.filter(user=request.user, category=category).first()
        value = request.data.get("monthly_alert_threshold")
        form = CategoryLimitForm(
            {"monthly_alert_threshold": "" if value is None else value},
            instance=override or CategoryOverride(user=request.user, category=category),
        )
        if not form.is_valid():
            return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
        form.save()
        return Response(self.get_serializer(category).data)
