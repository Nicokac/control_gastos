"""
Modelo Income para registro de ingresos.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.core.mixins import TimestampMixin, SoftDeleteMixin, CurrencyMixin
from apps.core.constants import CategoryType


# Create your models here.
class Income(TimestampMixin, SoftDeleteMixin, CurrencyMixin, models.Model):
    """
    Registro de ingresos del usuario.

    Hereda de:
    - TimestamMixin: created_at, updated_at
    - SoftDeleteMixin: is_active, deleted_at, soft_delte()
    - CurrencyMixin: amount, currency, exchange_rate, amount_ars
    """

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='income',
        verbose_name='Usuario'
    )
    date = models.DateField(
        verbose_name='Fecha'
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.PROTECT,
        related_name='incomes',
        verbose_name='Categoría'
    )
    description = models.CharField(
        max_length=255,
        verbose_name='Descripción'
    )
    is_recurring = models.BooleanField(
        default=False,
        verbose_name='Es recurrente'
    )

    class Meta:
        verbose_name = 'Ingreso'
        verbose_name_plural = 'Ingreso'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['date', 'is_active']),
        ]

    def __str__(self):
        return f"{self.description} - {self.formatted_amount} ({self.date})"
    
    def clean(self):
        """Validaciones del modelo."""
        super().clean()

        # Validar que el monto sea positivo
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({
                'amount': 'El monto debe ser mayor a cero.'
            })
        
    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_user_incomes(cls, user, month=None, year=None):
        """Obtiene los ingresos de un usuario, opcionalmente filtrados por mes/año

        Args:
            user: Usuario
            month: Mes (1-12)
            year: Año

        Returns:
            QuerySet de ingresos
        """
        queryset = cls.objects.filter(user=user)

        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)

        return queryset.select_related('category')
    
    @classmethod
    def get_monthly_total(cls, user, month, year):
        """
        Calcula el total de ingresos de un mes.
        
        Args:
            user: Usuario
            month: Mes (1-12)
            year: Año

        Returns:
            Decimal con el total
        """
        from django.db.models import Sum

        result = cls.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
            is_active=True
        ).aggregate(total=Sum('amount_ars'))

        return result['total'] or Decimal('0')
    
    @classmethod
    def get_by_category(cls, user, month, year):
        """
        Obtiene ingresos agrupados por categoría.
        
        Args:
            user: Usuario
            month: Mes (1-12)
            year: Año
        
        Returns:
            QuerySet con categoría y total
        """
        from django.db.models import Sum

        return cls.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
            is_active=True
        ).values(
            'category__id',
            'category__name',
            'category__icon',
            'category__color',
        ).annotate(
            total=Sum('amount.ars')
        ).order_by('-total')
