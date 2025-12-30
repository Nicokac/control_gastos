"""Managers personalizados para modelos con soft delete."""

from django.db import models


class SoftDeleteManager(models.Manager):
    """Manger que filtra automáticamente los registros eliminados."""

    def get_queryset(self):
        """Retorna solo registros activos por defecto."""
        return super().get_queryset().filter(is_active=True)

    def all_with_deleted(self):
        """Retorna todos los registros, incluyendo eliminados."""
        return super().get_queryset()

    def deleted_only(self):
        """Retorna solo los registros eliminados."""
        return super().get_queryset().filter(is_active=False)
