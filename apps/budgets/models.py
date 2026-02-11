"""
Modelo Budget para presupuestos mensuales.
"""

import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum

from apps.core.constants import CategoryType
from apps.core.mixins import SoftDeleteMixin, TimestampMixin


class Budget(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Presupuesto mensual por categoría.

    Hereda de:
    - TimestampMixin: created_at, updated_at
    - SoftDeleteMixin: is_active, deleted_at, soft_delete()
    """

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="budgets", verbose_name="Usuario"
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="budgets",
        verbose_name="Categoría",
    )
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)], verbose_name="Mes"
    )
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2020), MaxValueValidator(2100)], verbose_name="Año"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Monto presupuestado",
    )
    alert_threshold = models.PositiveSmallIntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Umbral de alerta (%)",
        help_text="Porcentaje del presupuesto a partir del cual se muestra alerta",
    )
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ["-year", "-month", "category__name"]
        # Un presupuesto por categoría por mes/año por usuario
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "month", "year"],
                name="unique_budget_per_category_month",
            )
        ]
        indexes = [
            models.Index(fields=["user", "year", "month", "is_active"]),
            models.Index(fields=["user", "category"]),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.month_name} {self.year}"

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

        # Validar que la categoría sea de tipo EXPENSE
        if self.category_id:
            from apps.categories.models import Category

            try:
                category = Category.objects.get(pk=self.category_id)
                if category.type != CategoryType.EXPENSE:
                    raise ValidationError(
                        {"category": "Solo se pueden crear presupuestos para categorías de gasto."}
                    )
            except Category.DoesNotExist:
                logger = logging.getLogger("apps.budgets")
                logger.warning(f"Budget.clean(): Category {self.category_id} no existe")

    @property
    def month_name(self):
        """Retorna el nombre del mes."""
        from apps.core.utils import get_month_name

        return get_month_name(self.month)

    @property
    def period_display(self):
        """Retorna el período formateado."""
        return f"{self.month_name} {self.year}"

    @property
    def spent_amount(self):
        """
        Calcula el monto gastado en el período para esta categoría.

        Si el QuerySet fue anotado con 'spent', usa ese valor para evitar N+1.
        De lo contrario, calcula on-the-fly (fallback).
        """
        # Si ya está anotado (desde el QuerySet), usar ese valor
        if hasattr(self, "_spent_annotated"):
            return self._spent_annotated or Decimal("0")

        # Fallback: calcular on-the-fly
        from apps.expenses.models import Expense

        result = Expense.objects.filter(
            user=self.user,
            category=self.category,
            date__month=self.month,
            date__year=self.year,
            is_active=True,
        ).aggregate(total=Sum("amount_ars"))

        return result["total"] or Decimal("0")

    @property
    def remaining_amount(self):
        """Calcula el monto restante del presupuesto."""
        remaining = self.amount - self.spent_amount
        return remaining

    @property
    def spent_percentage(self):
        """Calcula el porcentaje gastado."""
        if self.amount <= 0:
            return 0
        percentage = (self.spent_amount / self.amount) * 100
        return round(percentage, 1)

    @property
    def is_over_budget(self):
        """Indica si se superó el presupuesto."""
        return self.spent_amount > self.amount

    @property
    def is_near_limit(self):
        """Indica si está cerca del límite (supera el umbral de alerta)."""
        return self.spent_percentage >= self.alert_threshold and not self.is_over_budget

    @property
    def status(self):
        """Retorna el estado del presupuesto."""
        if self.is_over_budget:
            return "over"
        elif self.is_near_limit:
            return "warning"
        else:
            return "ok"

    @property
    def status_class(self):
        """Retorna la clase CSS según el estado."""
        status_classes = {"over": "danger", "warning": "warning", "ok": "success"}
        return status_classes.get(self.status, "secondary")

    @property
    def formatted_amount(self):
        """Retorna el monto presupuestado formateado."""
        return f"$ {self.amount:,.2f}"

    @property
    def formatted_spent(self):
        """Retorna el monto gastado formateado."""
        return f"$ {self.spent_amount:,.2f}"

    @property
    def formatted_remaining(self):
        """Retorna el monto restante formateado."""
        remaining = self.remaining_amount
        if remaining < 0:
            return f"-$ {abs(remaining):,.2f}"
        return f"$ {remaining:,.2f}"

    @classmethod
    def get_user_budgets(cls, user, month=None, year=None):
        """
        Obtiene los presupuestos de un usuario.

        Args:
            user: Usuario
            month: Mes (1-12)
            year: Año

        Returns:
            QuerySet de presupuestos
        """
        queryset = cls.objects.filter(user=user)

        if month and year:
            queryset = queryset.filter(month=month, year=year)
        elif year:
            queryset = queryset.filter(year=year)

        return queryset.select_related("category")

    @classmethod
    def get_current_month_budgets(cls, user):
        """
        Obtiene los presupuestos del mes actual.

        Args:
            user: Usuario

        Returns:
            QuerySet de presupuestos
        """
        from django.utils import timezone

        today = timezone.now().date()
        return cls.get_user_budgets(user, month=today.month, year=today.year)

    @classmethod
    def get_monthly_summary(cls, user, month, year):
        """
        Obtiene un resumen de presupuestos del mes.

        Args:
            user: Usuario
            month: Mes (1-12)
            year: Año

        Returns:
            Dict con totales
        """
        budgets = cls.get_user_budgets(user, month=month, year=year)

        total_budgeted = sum(b.amount for b in budgets)
        total_spent = sum(b.spent_amount for b in budgets)

        return {
            "total_budgeted": total_budgeted,
            "total_spent": total_spent,
            "total_remaining": total_budgeted - total_spent,
            "overall_percentage": round((total_spent / total_budgeted * 100), 1)
            if total_budgeted > 0
            else 0,
            "budget_count": budgets.count(),
            "over_budget_count": sum(1 for b in budgets if b.is_over_budget),
            "warning_count": sum(1 for b in budgets if b.is_near_limit),
        }

    @classmethod
    def copy_from_previous_month(cls, user, target_month, target_year):
        """
        Copia los presupuestos del mes anterior al mes objetivo.

        Optimizado: usa bulk_create y evita N+1 queries.

        Args:
            user: Usuario
            target_month: Mes destino (1-12)
            target_year: Año destino

        Returns:
            Lista de presupuestos creados
        """
        # Calcular mes anterior
        if target_month == 1:
            source_month = 12
            source_year = target_year - 1
        else:
            source_month = target_month - 1
            source_year = target_year

        # Obtener presupuestos del mes anterior (1 query)
        source_budgets = list(
            cls.objects.filter(
                user=user, month=source_month, year=source_year, is_active=True
            ).select_related("category")
        )

        if not source_budgets:
            return []

        # Obtener categorías que YA tienen presupuesto en el mes destino (1 query)
        existing_category_ids = set(
            cls.objects.filter(user=user, month=target_month, year=target_year).values_list(
                "category_id", flat=True
            )
        )

        # Preparar presupuestos a crear (solo los que no existen)
        budgets_to_create = []
        for budget in source_budgets:
            if budget.category_id not in existing_category_ids:
                budgets_to_create.append(
                    cls(
                        user=user,
                        category=budget.category,
                        month=target_month,
                        year=target_year,
                        amount=budget.amount,
                        alert_threshold=budget.alert_threshold,
                        notes=f"Copiado de {budget.period_display}",
                    )
                )

        # Crear todos de una vez (1 query)
        if budgets_to_create:
            created = cls.objects.bulk_create(budgets_to_create)
            return created

        return []

    @classmethod
    def get_with_spent(cls, user, month=None, year=None):
        """
        Obtiene presupuestos con spent_amount pre-calculado (evita N+1).

        Args:
            user: Usuario
            month: Mes (1-12)
            year: Año

        Returns:
            QuerySet de presupuestos con _spent_annotated
        """
        from django.db.models import OuterRef, Subquery, Sum
        from django.db.models.functions import Coalesce

        from apps.expenses.models import Expense

        # Subquery para calcular spent por cada budget
        spent_subquery = (
            Expense.objects.filter(
                user=user,
                category=OuterRef("category"),
                date__month=OuterRef("month"),
                date__year=OuterRef("year"),
                is_active=True,
            )
            .values("category")
            .annotate(total=Sum("amount_ars"))
            .values("total")
        )

        queryset = cls.objects.filter(user=user).select_related("category")

        # Filtrar por período si se especifica
        if month and year:
            queryset = queryset.filter(month=month, year=year)
        elif year:
            queryset = queryset.filter(year=year)

        # Anotar con spent
        queryset = queryset.annotate(
            _spent_annotated=Coalesce(Subquery(spent_subquery), Decimal("0"))
        )

        return queryset
