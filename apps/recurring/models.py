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
    total_installments = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Cantidad de cuotas",
        help_text="Dejá vacío si el gasto no tiene fecha de fin (servicios, alquiler, etc.).",
    )
    starting_installment = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Cuota de inicio",
        help_text="Número de cuota desde la que empezás a registrar (por defecto 1).",
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Mes de inicio",
        help_text="Primer mes en que aplica este gasto (para el conteo de cuotas).",
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
    def is_installment(self):
        return self.total_installments is not None

    @property
    def installments_paid(self):
        if not self.is_installment or not self.start_date:
            return None
        offset = (self.starting_installment or 1) - 1
        return offset + self.expenses.count()

    @property
    def installments_remaining(self):
        if not self.is_installment:
            return None
        paid = self.installments_paid or 0
        return max(self.total_installments - paid, 0)

    def auto_deactivate_if_complete(self):
        """Desactiva el gasto si ya se pagaron todas las cuotas."""
        if self.is_installment and self.is_active:
            paid = self.installments_paid or 0
            if paid >= self.total_installments:
                self.is_active = False
                self.save(update_fields=["is_active"])

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
