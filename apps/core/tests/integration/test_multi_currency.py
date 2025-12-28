"""
Tests de integración para escenarios multi-moneda.
"""

import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse

from apps.expenses.models import Expense
from apps.income.models import Income
from apps.core.constants import Currency


@pytest.mark.django_db
class TestMultiCurrencyExpenses:
    """Tests de gastos multi-moneda."""

    def test_ars_expense_has_exchange_rate_one(
        self, authenticated_client, user, expense_category
    ):
        """Verifica que gasto en ARS tenga exchange_rate = 1."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto ARS',
            'amount': '1000.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        expense = Expense.objects.get(description='Gasto ARS')
        assert expense.exchange_rate == Decimal('1')
        assert expense.amount_ars == Decimal('1000.00')

    def test_usd_expense_converts_correctly(
        self, authenticated_client, user, expense_category
    ):
        """Verifica conversión correcta de USD a ARS."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto USD',
            'amount': '100.00',
            'currency': Currency.USD,
            'exchange_rate': '1150.50',
            'date': date.today().isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        expense = Expense.objects.get(description='Gasto USD')
        assert expense.currency == Currency.USD
        assert expense.amount == Decimal('100.00')
        assert expense.exchange_rate == Decimal('1150.50')
        assert expense.amount_ars == Decimal('115050.00')

    def test_mixed_currency_expenses_in_same_budget(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """Verifica que presupuesto sume correctamente gastos mixtos."""
        today = date.today()
        
        budget = budget_factory(
            user, expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('200000.00')
        )
        
        create_url = reverse('expenses:create')
        
        # Gasto en ARS
        authenticated_client.post(create_url, {
            'category': expense_category.pk,
            'description': 'Gasto ARS',
            'amount': '50000.00',
            'currency': Currency.ARS,
            'date': today.isoformat(),
        })
        
        # Gasto en USD
        authenticated_client.post(create_url, {
            'category': expense_category.pk,
            'description': 'Gasto USD',
            'amount': '100.00',
            'currency': Currency.USD,
            'exchange_rate': '1000.00',
            'date': today.isoformat(),
        })
        
        # Presupuesto debería sumar en ARS
        budget.refresh_from_db()
        # 50000 ARS + (100 USD * 1000) = 150000 ARS
        assert budget.spent_amount == Decimal('150000.00')


@pytest.mark.django_db
class TestMultiCurrencyIncome:
    """Tests de ingresos multi-moneda."""

    def test_ars_income_has_exchange_rate_one(
        self, authenticated_client, user, income_category
    ):
        """Verifica que ingreso en ARS tenga exchange_rate = 1."""
        create_url = reverse('income:create')
        data = {
            'category': income_category.pk,
            'description': 'Sueldo ARS',
            'amount': '150000.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        income = Income.objects.get(description='Sueldo ARS')
        assert income.exchange_rate == Decimal('1')
        assert income.amount_ars == Decimal('150000.00')

    def test_usd_income_converts_correctly(
        self, authenticated_client, user, income_category
    ):
        """Verifica conversión correcta de ingreso USD a ARS."""
        create_url = reverse('income:create')
        data = {
            'category': income_category.pk,
            'description': 'Freelance USD',
            'amount': '1000.00',
            'currency': Currency.USD,
            'exchange_rate': '1200.00',
            'date': date.today().isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        income = Income.objects.get(description='Freelance USD')
        assert income.currency == Currency.USD
        assert income.amount_ars == Decimal('1200000.00')


@pytest.mark.django_db
class TestExchangeRateEdgeCases:
    """Tests de casos límite con tipos de cambio."""

    def test_very_high_exchange_rate(
        self, authenticated_client, user, expense_category
    ):
        """Verifica manejo de tipo de cambio alto."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto Cambio Alto',
            'amount': '10.00',
            'currency': Currency.USD,
            'exchange_rate': '9999.99',
            'date': date.today().isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        expense = Expense.objects.get(description='Gasto Cambio Alto')
        assert expense.amount_ars == Decimal('99999.90')

    def test_decimal_exchange_rate(
        self, authenticated_client, user, expense_category
    ):
        """Verifica manejo de tipo de cambio decimal."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto Decimal',
            'amount': '100.00',
            'currency': Currency.USD,
            'exchange_rate': '1234.56',
            'date': date.today().isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        expense = Expense.objects.get(description='Gasto Decimal')
        assert expense.amount_ars == Decimal('123456.00')