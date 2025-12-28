"""
Tests para los formularios de Income.
"""

import pytest
from decimal import Decimal
from django.utils import timezone

from apps.income.forms import IncomeForm
from apps.income.models import Income
from apps.core.constants import Currency


@pytest.mark.django_db
class TestIncomeForm:
    """Tests para IncomeForm."""

    def test_valid_income_ars(self, user, income_category):
        """Verifica formulario válido para ingreso en ARS."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Sueldo mensual',
                'amount': '150000.00',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert form.is_valid(), form.errors

    def test_valid_income_usd(self, user, income_category):
        """Verifica formulario válido para ingreso en USD."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Freelance',
                'amount': '500.00',
                'currency': Currency.USD,
                'exchange_rate': '1150.00',
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert form.is_valid(), form.errors

    def test_category_required(self, user):
        """Verifica que la categoría sea requerida."""
        form = IncomeForm(
            data={
                'description': 'Test',
                'amount': '100.00',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'category' in form.errors

    def test_description_required(self, user, income_category):
        """Verifica que la descripción sea requerida."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': '',
                'amount': '100.00',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'description' in form.errors

    def test_amount_required(self, user, income_category):
        """Verifica que el monto sea requerido."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Test',
                'amount': '',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_date_required(self, user, income_category):
        """Verifica que la fecha sea requerida."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Test',
                'amount': '100.00',
                'currency': Currency.ARS,
                'date': '',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'date' in form.errors

    def test_negative_amount_invalid(self, user, income_category):
        """Verifica que monto negativo sea inválido."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Test',
                'amount': '-100.00',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_zero_amount_invalid(self, user, income_category):
        """Verifica que monto cero sea inválido."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Test',
                'amount': '0',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_usd_requires_exchange_rate(self, user, income_category):
        """Verifica que USD requiera tipo de cambio."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Ingreso USD',
                'amount': '100.00',
                'currency': Currency.USD,
                'exchange_rate': '',
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'exchange_rate' in form.errors or '__all__' in form.errors

    def test_ars_ignores_exchange_rate(self, user, income_category):
        """Verifica que ARS ignore tipo de cambio."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Ingreso ARS',
                'amount': '100.00',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestIncomeFormCategories:
    """Tests para filtrado de categorías en IncomeForm."""

    def test_only_user_income_categories(self, user, expense_category, income_category):
        """Verifica que solo muestre categorías de ingreso del usuario."""
        form = IncomeForm(user=user)
        
        category_queryset = form.fields['category'].queryset
        
        # Debe incluir categoría de ingreso
        assert income_category in category_queryset
        
        # No debe incluir categoría de gasto
        assert expense_category not in category_queryset

    def test_excludes_other_user_categories(self, user, other_user, income_category_factory):
        """Verifica que excluya categorías de otros usuarios."""
        cat_other = income_category_factory(other_user, name='Otra')
        
        form = IncomeForm(user=user)
        category_queryset = form.fields['category'].queryset
        
        assert cat_other not in category_queryset


@pytest.mark.django_db
class TestIncomeFormSave:
    """Tests para guardado de IncomeForm."""

    def test_save_creates_income(self, user, income_category):
        """Verifica que save() cree el ingreso."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Nuevo ingreso',
                'amount': '50000.00',
                'currency': Currency.ARS,
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert form.is_valid(), form.errors
        
        income = form.save(commit=False)
        income.user = user
        income.save()
        
        assert income.pk is not None
        assert income.amount == Decimal('50000.00')
        assert income.user == user

    def test_save_calculates_amount_ars(self, user, income_category):
        """Verifica que save() calcule amount_ars para USD."""
        form = IncomeForm(
            data={
                'category': income_category.pk,
                'description': 'Ingreso USD',
                'amount': '500.00',
                'currency': Currency.USD,
                'exchange_rate': '1200.00',
                'date': timezone.now().date(),
            },
            user=user
        )
        
        assert form.is_valid(), form.errors
        
        income = form.save(commit=False)
        income.user = user
        income.save()
        
        assert income.amount_ars == Decimal('600000.00')