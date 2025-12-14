"""
Mixin reutilizables para modelos Django.
"""
from .managers import SoftDeleteManager
from decimal import Decimal
from django.db import models
from django.utils import timezone

from .constants import Currency, DEFAULT_EXCHANGE_RATE


class TimestampMixin(models.Model):
    """
    Mixin que agrega campos de auditoría de tiempo.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificación'
    )

    class Meta:
        abstract = True

class SoftDeleteMixin(models.Model):
    """
    Mixin para eliminación lógica (soft delete).
    Los registros no se eliminan físicamente, se marcan como inactivos.
    """
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de eliminación'
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        """Marca el registro como eliminado."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])

    def restore(self):
        """Restaura un registro eliminado."""
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at'])

    def hard_delete(self):
        """Elimina el registro permanentemente."""
        super().delete()


class CurrencyMixin(models.Model):
    """
    Mixin para modelos que manejan montos con soporte multimoneda.
    Calcula automáticamente el monto en ARS para totalizaciones.
    """
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Monto'
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.ARS,
        verbose_name='Moneda'
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=DEFAULT_EXCHANGE_RATE,
        verbose_name='Tasa de cambio'
    )
    amount_ars = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        verbose_name='Monto en ARS'
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Calcula amount_ars antes de guardar."""
        self._calculate_amount_ars()
        super().save(*args, **kwargs)

    def _calculate_amount_ars(self):
        """
        Calcula el monto en ARS según la moneda.
        Si es ARS, amount_ars = amount.
        Si es USD, amount_ars = amount * exchange_rate.
        """
        if self.currency == Currency.ARS:
            self.amount_ars = self.amount
        else:
            self.amount_ars = self.amount * self.exchange_rate

    @property
    def formatted_amount(self):
        """Retorna el monto formateado con símbolo de moneda."""
        symbol = '$' if self.currency == Currency.ARS else 'US$'
        return f"{symbol} {self.amount:,.2f}"

    @property
    def formatted_amount_ars(self):
        """Retorna el monto en ARS formateado."""
        return f"$ {self.amount_ars:,.2f}"


class UserOwnedMixin(models.Model):
    """
    Mixin para modelos que pertenecen a un usuario.
    Requiere que el modelo User esté definido.
    """
    # Se define como string para evitar imports circulares
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='Usuario'
    )

    class Meta:
        abstract = True