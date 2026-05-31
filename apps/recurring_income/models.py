"""Modelo RecurringIncome para ingresos fijos mensuales."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.mixins import TimestampMixin


class RecurringIncome(TimestampMixin, models.Model):
    """
    Plantilla de ingreso recurrente mensual.

    Representa un ingreso que se repite cada mes (sueldo, alquiler cobrado, freelance fijo, etc.).
    No registra el cobro — eso lo hace Income. Sirve como recordatorio y referencia del último monto cobrado.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="recurring_incomes",
        verbose_name="Usuario",
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="recurring_incomes",
        verbose_name="Categoría",
        help_text="Categoría de ingreso a la que pertenece.",
    )
    expected_day = models.PositiveSmallIntegerField(
        verbose_name="Día esperado de cobro",
        help_text="Día del mes en que solés cobrar este ingreso (1-31).",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notes = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Notas",
        help_text="Referencia opcional (ej: empresa, cliente).",
    )

    class Meta:
        verbose_name = "Ingreso recurrente"
        verbose_name_plural = "Ingresos recurrentes"
        ordering = ["expected_day", "name"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} (día {self.expected_day})"

    @property
    def last_income(self):
        """Último Income vinculado a este recurrente."""
        return self.incomes.select_related("category").order_by("-date").first()

    def is_collected_in(self, month, year):
        """Verdadero si hay al menos un Income vinculado en el mes/año dado."""
        return self.incomes.filter(date__month=month, date__year=year).exists()

    def status_for(self, month, year):
        """
        Estado del recurrente para un mes/año:
        - 'collected': ya tiene cobro registrado ese mes
        - 'overdue': no cobrado y el día esperado ya pasó (mes actual)
        - 'pending': no cobrado y aún no llegó el día (mes actual) o mes futuro
        """
        from django.utils import timezone

        if self.is_collected_in(month, year):
            return "collected"

        today = timezone.localdate()
        if year < today.year or (year == today.year and month < today.month):
            return "overdue"
        if year == today.year and month == today.month and today.day > self.expected_day:
            return "overdue"
        return "pending"
