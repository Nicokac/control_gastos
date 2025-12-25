"""
Modelo Budget para presupuestos mensuales.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum, F
from decimal import Decimal

from apps.core.mixins import TimestampMixin, SoftDeleteMixin
from apps.core.constants import CategoryType


class Budget(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Presupuesto mensual por categoría.
    
    Hereda de:
    - TimestampMixin: created_at, updated_at
    - SoftDeleteMixin: is_active, deleted_at, soft_delete()
    """
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='Usuario'
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.PROTECT,
        related_name='budgets',
        verbose_name='Categoría'
    )
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name='Mes'
    )
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2020), MaxValueValidator(2100)],
        verbose_name='Año'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto presupuestado'
    )
    alert_threshold = models.PositiveSmallIntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Umbral de alerta (%)',
        help_text='Porcentaje del presupuesto a partir del cual se muestra alerta'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Notas'
    )

    class Meta:
        verbose_name = 'Presupuesto'
        verbose_name_plural = 'Presupuestos'
        ordering = ['-year', '-month', 'category__name']
        # Un presupuesto por categoría por mes/año por usuario
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month', 'year'],
                name='unique_budget_per_category_month'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'month', 'year']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f"{self.category.name} - {self.month_name} {self.year}"

    def clean(self):
        """Validaciones del modelo."""
        super().clean()
        
        # Validar que el monto sea positivo
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({
                'amount': 'El monto debe ser mayor a cero.'
            })
        
        # Validar que la categoría sea de tipo EXPENSE
        if self.category_id:
            from apps.categories.models import Category
            try:
                category = Category.objects.get(pk=self.category_id)
                if category.type != CategoryType.EXPENSE:
                    raise ValidationError({
                        'category': 'Solo se pueden crear presupuestos para categorías de gasto.'
                    })
            except Category.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

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
        """Calcula el monto gastado en el período para esta categoría."""
        from apps.expenses.models import Expense
        
        result = Expense.objects.filter(
            user=self.user,
            category=self.category,
            date__month=self.month,
            date__year=self.year,
            is_active=True
        ).aggregate(total=Sum('amount_ars'))
        
        return result['total'] or Decimal('0')

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
            return 'over'
        elif self.is_near_limit:
            return 'warning'
        else:
            return 'ok'

    @property
    def status_class(self):
        """Retorna la clase CSS según el estado."""
        status_classes = {
            'over': 'danger',
            'warning': 'warning',
            'ok': 'success'
        }
        return status_classes.get(self.status, 'secondary')

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
        
        return queryset.select_related('category')

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
            'total_budgeted': total_budgeted,
            'total_spent': total_spent,
            'total_remaining': total_budgeted - total_spent,
            'overall_percentage': round((total_spent / total_budgeted * 100), 1) if total_budgeted > 0 else 0,
            'budget_count': budgets.count(),
            'over_budget_count': sum(1 for b in budgets if b.is_over_budget),
            'warning_count': sum(1 for b in budgets if b.is_near_limit),
        }

    @classmethod
    def copy_from_previous_month(cls, user, target_month, target_year):
        """
        Copia los presupuestos del mes anterior al mes objetivo.
        
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
        
        # Obtener presupuestos del mes anterior
        source_budgets = cls.objects.filter(
            user=user,
            month=source_month,
            year=source_year,
            is_active=True
        )
        
        created = []
        for budget in source_budgets:
            # Verificar que no exista ya
            if not cls.objects.filter(
                user=user,
                category=budget.category,
                month=target_month,
                year=target_year
            ).exists():
                new_budget = cls.objects.create(
                    user=user,
                    category=budget.category,
                    month=target_month,
                    year=target_year,
                    amount=budget.amount,
                    alert_threshold=budget.alert_threshold,
                    notes=f"Copiado de {budget.period_display}"
                )
                created.append(new_budget)
        
        return created