from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.api.v1.serializers.categories import CategorySerializer
from apps.categories.models import Category
from apps.core.constants import CategoryType


class CategoryPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 500


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    pagination_class = CategoryPagination

    def get_queryset(self):
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
