"""Modelo RecurringExpense para gastos fijos mensuales."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.mixins import TimestampMixin


class RecurringExpense(TimestampMixin, models.Model):
    """
    Plantilla de gasto recurrente mensual.

    Representa un gasto que se repite cada mes (servicio, impuesto, cuota, etc.).
    No registra el pago — eso lo hace Expense. Sirve como recordatorio
    y referencia del último monto pagado.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="recurring_expenses",
        verbose_name="Usuario",
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="recurring_expenses",
        verbose_name="Categoría",
        help_text="Subcategoría de gasto a la que pertenece.",
    )
    due_day = models.PositiveSmallIntegerField(
        verbose_name="Día de vencimiento",
        help_text="Día del mes en que vence o se suele pagar (1-31).",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    notes = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Notas",
        help_text="Referencia opcional (ej: número de cuenta, proveedor).",
    )

    class Meta:
        verbose_name = "Gasto recurrente"
        verbose_name_plural = "Gastos recurrentes"
        ordering = ["due_day", "name"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} (día {self.due_day})"

    @property
    def last_expense(self):
        """Último Expense vinculado a este recurrente."""
        return self.expenses.select_related("category").order_by("-date").first()

    def is_paid_in(self, month, year):
        """Verdadero si hay al menos un Expense vinculado en el mes/año dado."""
        return self.expenses.filter(date__month=month, date__year=year).exists()

    def status_for(self, month, year):
        """
        Estado del recurrente para un mes/año:
        - 'paid': ya tiene pago registrado ese mes
        - 'overdue': no pagado y el día de vencimiento ya pasó (mes actual)
        - 'pending': no pagado y aún no venció (mes actual) o mes futuro
        """
        from django.utils import timezone

        if self.is_paid_in(month, year):
            return "paid"

        today = timezone.localdate()
        if year < today.year or (year == today.year and month < today.month):
            return "overdue"
        if year == today.year and month == today.month and today.day > self.due_day:
            return "overdue"
        return "pending"
