"""Modelo Expense para registro de gastos."""

from contextlib import suppress
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.constants import ExpenseType, PaymentMethod
from apps.core.mixins import CurrencyMixin, SoftDeleteMixin, TimestampMixin


# Create your models here.
class Expense(TimestampMixin, SoftDeleteMixin, CurrencyMixin, models.Model):
    """
    Registro de gastos del usuario.

    Hereda de:
    - TimestamMixin: created_at, updated_at
    - SoftDeleteMixin: is_activa, deleted_at, soft_delete()
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
            models.Index(fields=["user", "is_active", "date"]),
        ]

    def __str__(self):
        return f"{self.description} - {self.formatted_amount} ({self.date})"

    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.full_clean()

        is_new = self.pk is None
        old_saving_id = None
        old_amount = None

        # Si es update, guardar valores anteriores
        if not is_new:
            old = Expense.objects.filter(pk=self.pk).values("saving_id", "amount_ars").first()
            if old:
                old_saving_id = old["saving_id"]
                old_amount = old["amount_ars"]

        super().save(*args, **kwargs)

        # Sincronizar con Saving
        self._sync_saving(is_new, old_saving_id, old_amount)

    def _sync_saving(self, is_new, old_saving_id, old_amount):
        """Sincroniza el gasto con el ahorro vinculado."""
        if is_new and self.saving:
            # Nuevo gasto → depositar
            self.saving.add_deposit(
                amount=self.amount_ars, description=f"Desde gasto: {self.description}"
            )
        elif not is_new:
            # Update: manejar cambios
            if old_saving_id == self.saving_id and self.saving and old_amount != self.amount_ars:
                # Mismo ahorro, monto cambió → ajustar diferencia
                diff = self.amount_ars - old_amount
                if diff > 0:
                    self.saving.add_deposit(diff, f"Ajuste: {self.description}")
                elif diff < 0:
                    self.saving.add_withdrawal(abs(diff), f"Ajuste: {self.description}")
            elif old_saving_id != self.saving_id:
                # Cambió el ahorro destino
                if old_saving_id:
                    from apps.savings.models import Saving

                    old_saving = Saving.objects.filter(pk=old_saving_id).first()
                    if old_saving:
                        with suppress(ValueError):
                            old_saving.add_withdrawal(old_amount, f"Reasignado: {self.description}")

                if self.saving:
                    # Agregar al nuevo ahorro
                    self.saving.add_deposit(self.amount_ars, f"Desde gasto: {self.description}")

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
                pass

    def soft_delete(self):
        """Elimina el gasto y revierte el depósito si estaba vinculado."""
        if self.saving and self.is_active:
            with suppress(ValueError):
                self.saving.add_withdrawal(
                    amount=self.amount_ars, description=f"Gasto eliminado: {self.description}"
                )
        super().soft_delete()

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

        result = cls.objects.filter(
            user=user, date__month=month, date__year=year, is_active=True
        ).aggregate(total=Sum("amount_ars"))

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
            cls.objects.filter(user=user, date__month=month, date__year=year, is_active=True)
            .values("category__id", "category__name", "category__icon", "category__color")
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")
        )
