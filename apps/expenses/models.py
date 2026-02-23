"""Modelo Expense para registro de gastos."""

import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.constants import ExpenseType, PaymentMethod
from apps.core.mixins import CurrencyMixin, TimestampMixin


# Create your models here.
class Expense(TimestampMixin, CurrencyMixin, models.Model):
    """
    Registro de gastos del usuario.

    Hereda de:
    - TimestampMixin: created_at, updated_at
    - CurrencyMixin: amount, currency, exchange_rate, amount_ars
    """

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="expense", verbose_name="Usuario"
    )
    date = models.DateField(verbose_name="Fecha")
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="expenses",
        verbose_name="Categoría",
    )
    description = models.CharField(max_length=255, verbose_name="Descripción")
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        blank=True,
        default="",
        verbose_name="Método de pago",
    )
    expense_type = models.CharField(
        max_length=10,
        choices=ExpenseType.choices,
        blank=True,
        default="",
        verbose_name="Tipo de gasto",
    )
    saving = models.ForeignKey(
        "savings.Saving",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_expenses",
        verbose_name="Destino de ahorro",
        help_text="Si se selecciona, este gasto se suma automáticamente al ahorro",
    )

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self):
        return f"{self.description} - {self.formatted_amount} ({self.date})"

    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Validaciones del modelo."""
        super().clean()

        # Validar que el monto sea positivo
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "El monto debe ser mayor a cero."})

        # Validar que la categoría sea de tipo EXPENSE (seguridad para admin/shell)
        if self.category_id:
            from apps.categories.models import Category
            from apps.core.constants import CategoryType

            try:
                category = Category.objects.get(pk=self.category_id)
                if category.type != CategoryType.EXPENSE:
                    raise ValidationError({"category": "La categoría debe ser de tipo Gasto."})
            except Category.DoesNotExist:
                logger = logging.getLogger("apps.expenses")
                logger.warning(f"Expense.clean(): Category {self.category_id} no existe")

    def delete(self, *args, **kwargs):
        """Elimina el gasto."""
        super().delete(*args, **kwargs)

    @classmethod
    def get_user_expenses(cls, user, month=None, year=None):
        """
        Obtiene los gastos de un usuario, opcionalmente filtrados por mes/año.

        Args:
            :param cls: Cls
            :param user: Usuario
            :param month: Mes (1-12)
            :param year: Año

        Returns:
            QuerySet de gastos
        """
        queryset = cls.objects.filter(user=user)

        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)

        return queryset.select_related("category")

    @classmethod
    def get_monthly_total(cls, user, month, year, currency="ARS"):
        """
        Calcula el total de gastos de un mes.

        Args:
            :param cls: Cls
            :param user: Usuario
            :param month: Mes (1-12)
            :param year: Año
            :param currency: Moneda para el total ('ARS' siempre usa amount_ars)

        Returns:
            Decimal con el total
        """
        from django.db.models import Sum

        result = cls.objects.filter(user=user, date__month=month, date__year=year).aggregate(
            total=Sum("amount_ars")
        )

        return result["total"] or Decimal("0")

    @classmethod
    def get_by_category(cls, user, month, year):
        """
        Obtiene gastos agrupados por categoría.

        :param cls: Cls
        :param user: Usuario
        :param month: Mes (1-12)
        :param year: Año

        Returns:
            QuerySet con categoría y total
        """
        from django.db.models import Sum

        return (
            cls.objects.filter(user=user, date__month=month, date__year=year)
            .values("category__id", "category__name", "category__icon", "category__color")
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")
        )
