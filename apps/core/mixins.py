"""
Mixin reutilizables para modelos Django.
"""

from decimal import Decimal

from django.db import models

from .constants import DEFAULT_EXCHANGE_RATE, Currency


class TimestampMixin(models.Model):
    """
    Mixin que agrega campos de auditoría de tiempo.
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    class Meta:
        abstract = True


class CurrencyMixin(models.Model):
    """
    Mixin para modelos que manejan montos con soporte multimoneda.
    Calcula automáticamente el monto en ARS para totalizaciones.
    """

    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.ARS, verbose_name="Moneda"
    )
    exchange_rate = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=DEFAULT_EXCHANGE_RATE,
        verbose_name="Tasa de cambio",
    )
    amount_ars = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        verbose_name="Monto en ARS",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Calcula amount_ars antes de guardar."""
        self._calculate_amount_ars()
        super().save(*args, **kwargs)

    def _calculate_amount_ars(self):
        """
        Calcula el monto en ARS.

        Fórmula unificada: amount * exchange_rate
        - ARS: exchange_rate = 1.0 → amount_ars = amount
        - USD: exchange_rate = cotización → amount_ars = amount * cotización
        """
        self.amount_ars = (self.amount * self.exchange_rate).quantize(Decimal("0.01"))

    @property
    def formatted_amount(self):
        symbol = "$" if self.currency == Currency.ARS else "US$"
        formatted = f"{self.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{symbol} {formatted}"

    @property
    def formatted_amount_ars(self):
        formatted = f"{self.amount_ars:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"$ {formatted}"


class UserOwnedMixin(models.Model):
    """
    Mixin para modelos que pertenecen a un usuario.
    Requiere que el modelo User esté definido.
    """

    # Se define como string para evitar imports circulares
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="%(class)ss", verbose_name="Usuario"
    )

    class Meta:
        abstract = True
