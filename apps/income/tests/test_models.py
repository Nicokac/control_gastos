"""
Tests para el modelo Income.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from apps.income.models import Income
from apps.core.constants import Currency


@pytest.mark.django_db
class TestIncomeModel:
    """Tests para el modelo Income."""

    def test_create_income_ars(self, user, income_category):
        """Verifica creación de ingreso en ARS."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description='Sueldo mensual',
            amount=Decimal('150000.00'),
            currency=Currency.ARS,
            exchange_rate=Decimal('1.00'),
            date=timezone.now().date()
        )
        
        assert income.pk is not None
        assert income.amount == Decimal('150000.00')
        assert income.currency == Currency.ARS
        assert income.amount_ars == Decimal('150000.00')

    def test_create_income_usd(self, user, income_category):
        """Verifica creación de ingreso en USD con conversión."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description='Freelance',
            amount=Decimal('500.00'),
            currency=Currency.USD,
            exchange_rate=Decimal('1150.00'),
            date=timezone.now().date()
        )
        
        assert income.currency == Currency.USD
        assert income.amount_ars == Decimal('575000.00')

    def test_income_str(self, income):
        """Verifica representación string."""
        result = str(income)
        
        assert income.description in result or str(income.amount) in result

    def test_income_formatted_amount(self, user, income_category):
        """Verifica formato de monto."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description='Test',
            amount=Decimal('50000.00'),
            currency=Currency.ARS,
            exchange_rate=Decimal('1.00'),
            date=timezone.now().date()
        )
        
        formatted = income.formatted_amount
        assert '$' in formatted or '50000' in formatted

    def test_income_belongs_to_user(self, income, user):
        """Verifica que el ingreso pertenece al usuario."""
        assert income.user == user

    def test_income_soft_delete(self, income):
        """Verifica soft delete de ingreso."""
        income_id = income.pk
        income.soft_delete()
        
        assert income.is_active is False
        assert Income.objects.filter(pk=income_id).exists() is False
        assert Income.all_objects.filter(pk=income_id).exists() is True

    def test_income_timestamps(self, income):
        """Verifica timestamps."""
        assert income.created_at is not None
        assert income.updated_at is not None


@pytest.mark.django_db
class TestIncomeCalculations:
    """Tests para cálculos de Income."""

    def test_amount_ars_calculation_usd(self, user, income_category):
        """Verifica cálculo de amount_ars para USD."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description='Test USD',
            amount=Decimal('100.00'),
            currency=Currency.USD,
            exchange_rate=Decimal('1200.00'),
            date=timezone.now().date()
        )
        
        assert income.amount_ars == Decimal('120000.00')

    def test_amount_ars_calculation_ars(self, user, income_category):
        """Verifica cálculo de amount_ars para ARS."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description='Test ARS',
            amount=Decimal('80000.00'),
            currency=Currency.ARS,
            exchange_rate=Decimal('1.00'),
            date=timezone.now().date()
        )
        
        assert income.amount_ars == Decimal('80000.00')


@pytest.mark.django_db
class TestIncomeQuerySet:
    """Tests para el QuerySet de Income."""

    def test_filter_by_user(self, user, other_user, income_category, income_category_factory, income_factory):
        """Verifica filtro por usuario."""
        inc_user1 = income_factory(user, income_category, description='User 1')
        
        other_category = income_category_factory(other_user, name='Salario Other')
        inc_user2 = income_factory(other_user, other_category, description='User 2')
        
        user_incomes = Income.objects.filter(user=user)
        
        assert inc_user1 in user_incomes
        assert inc_user2 not in user_incomes

    def test_filter_by_month_year(self, user, income_category, income_factory, today):
        """Verifica filtro por mes y año."""
        income = income_factory(user, income_category, date=today)
        
        month_incomes = Income.objects.filter(
            date__month=today.month,
            date__year=today.year
        )
        
        assert income in month_incomes

    def test_sum_total_income(self, user, income_category, income_factory):
        """Verifica suma total de ingresos."""
        from django.db.models import Sum
        
        income_factory(user, income_category, amount=Decimal('50000.00'))
        income_factory(user, income_category, amount=Decimal('30000.00'))
        
        total = Income.objects.filter(user=user).aggregate(
            total=Sum('amount_ars')
        )['total']
        
        assert total == Decimal('80000.00')

@pytest.mark.django_db
class TestIncomeValidations:
    """Tests de validaciones del modelo Income."""

    def test_negative_amount_raises_error(self, user, income_category):
        """Verifica que monto negativo lance error."""
        income = Income(
            user=user,
            category=income_category,
            description='Monto negativo',
            amount=Decimal('-100.00'),
            currency=Currency.ARS,
            exchange_rate=Decimal('1.00'),
            date=timezone.now().date()
        )
        
        with pytest.raises(ValidationError):
            income.full_clean()

    def test_zero_amount_raises_error(self, user, income_category):
        """Verifica que monto cero lance error."""
        income = Income(
            user=user,
            category=income_category,
            description='Monto cero',
            amount=Decimal('0.00'),
            currency=Currency.ARS,
            exchange_rate=Decimal('1.00'),
            date=timezone.now().date()
        )
        
        with pytest.raises(ValidationError):
            income.full_clean()

    def test_usd_requires_exchange_rate(self, user, income_category):
        """Verifica que USD requiera exchange_rate."""
        income = Income(
            user=user,
            category=income_category,
            description='Ingreso USD sin TC',
            amount=Decimal('100.00'),
            currency=Currency.USD,
            exchange_rate=None,
            date=timezone.now().date()
        )
        
        with pytest.raises((ValidationError, IntegrityError)):
            income.full_clean()
            income.save()

    def test_usd_exchange_rate_must_be_positive(self, user, income_category):
        """Verifica que exchange_rate sea positivo para USD."""
        income = Income(
            user=user,
            category=income_category,
            description='Ingreso USD TC cero',
            amount=Decimal('100.00'),
            currency=Currency.USD,
            exchange_rate=Decimal('0.00'),
            date=timezone.now().date()
        )
        
        with pytest.raises(ValidationError):
            income.full_clean()

    def test_ars_allows_default_exchange_rate(self, user, income_category):
        """Verifica que ARS permita exchange_rate por defecto."""
        income = Income(
            user=user,
            category=income_category,
            description='Ingreso ARS',
            amount=Decimal('100.00'),
            currency=Currency.ARS,
            exchange_rate=Decimal('1.00'),
            date=timezone.now().date()
        )
        
        # No debería lanzar error
        income.full_clean()
        income.save()
        
        assert income.pk is not None

    def test_description_required(self, user, income_category):
        """Verifica que descripción sea requerida."""
        income = Income(
            user=user,
            category=income_category,
            description='',  # Vacío
            amount=Decimal('100.00'),
            currency=Currency.ARS,
            exchange_rate=Decimal('1.00'),
            date=timezone.now().date()
        )
        
        with pytest.raises(ValidationError):
            income.full_clean()