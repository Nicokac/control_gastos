"""Modelos para gastos compartidos del hogar."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.mixins import CurrencyMixin, TimestampMixin


class HouseholdMember(TimestampMixin, models.Model):
    """Miembro del hogar del usuario (sin cuenta propia en la app)."""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="household_members",
        verbose_name="Usuario",
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")

    class Meta:
        verbose_name = "Miembro del hogar"
        verbose_name_plural = "Miembros del hogar"
        ordering = ["name"]
        unique_together = [("user", "name")]

    def __str__(self):
        return self.name


class SharedExpense(TimestampMixin, CurrencyMixin, models.Model):
    """
    Gasto compartido del hogar.

    paid_by = null  → pagó el dueño de la cuenta
    paid_by = <miembro> → pagó ese miembro
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="shared_expenses",
        verbose_name="Usuario",
    )
    date = models.DateField(verbose_name="Fecha")
    description = models.CharField(max_length=255, verbose_name="Descripción")
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="shared_expenses",
        verbose_name="Categoría",
    )
    paid_by = models.ForeignKey(
        HouseholdMember,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="paid_expenses",
        verbose_name="Pagado por",
        help_text="Dejá vacío si pagaste vos.",
    )

    class Meta:
        verbose_name = "Gasto compartido"
        verbose_name_plural = "Gastos compartidos"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="shared_expense_amount_positive",
            ),
        ]

    def __str__(self):
        payer = self.paid_by.name if self.paid_by else "Yo"
        return f"{self.description} — {payer} ({self.date})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "El monto debe ser mayor a cero."})

        if self.category_id:
            from apps.core.constants import CategoryType

            if self.category.type != CategoryType.EXPENSE:
                raise ValidationError({"category": "La categoría debe ser de tipo Gasto."})

        if self.paid_by_id and self.user_id and self.paid_by.user_id != self.user_id:
            raise ValidationError({"paid_by": "El miembro no pertenece a tu hogar."})

    @property
    def payer_name(self):
        return self.paid_by.name if self.paid_by else None
