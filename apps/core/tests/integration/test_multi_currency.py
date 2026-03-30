"""
Tests de integraciÃ³n para escenarios multi-moneda.
"""

from datetime import date
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.core.constants import Currency
from apps.expenses.models import Expense
from apps.income.models import Income


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestMultiCurrencyExpenses:
    """Tests de gastos multi-moneda."""

    def test_ars_expense_has_exchange_rate_one(self, authenticated_client, user, expense_category):
        """Verifica que gasto en ARS tenga exchange_rate = 1."""
        create_url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Gasto ARS",
            "amount": "1000.00",
            "currency": Currency.ARS,
            "date": date.today().isoformat(),
        }

        authenticated_client.post(create_url, data)

        expense = Expense.objects.get(description="Gasto ARS")
        assert expense.exchange_rate == Decimal("1")
        assert expense.amount_ars == Decimal("1000.00")

    def test_usd_expense_converts_correctly(self, authenticated_client, user, expense_category):
        """Verifica conversiÃ³n correcta de USD a ARS."""
        create_url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Gasto USD",
            "amount": "100.00",
            "currency": Currency.USD,
            "exchange_rate": "1150.50",
            "date": date.today().isoformat(),
        }

        authenticated_client.post(create_url, data)

        expense = Expense.objects.get(description="Gasto USD")
        assert expense.currency == Currency.USD
        assert expense.amount == Decimal("100.00")
        assert expense.exchange_rate == Decimal("1150.50")
        assert expense.amount_ars == Decimal("115050.00")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestMultiCurrencyIncome:
    """Tests de ingresos multi-moneda."""

    def test_ars_income_has_exchange_rate_one(self, authenticated_client, user, income_category):
        """Verifica que ingreso en ARS tenga exchange_rate = 1."""
        create_url = reverse("income:create")
        data = {
            "category": income_category.pk,
            "description": "Sueldo ARS",
            "amount": "150000.00",
            "currency": Currency.ARS,
            "date": date.today().isoformat(),
        }

        authenticated_client.post(create_url, data)

        income = Income.objects.get(description="Sueldo ARS")
        assert income.exchange_rate == Decimal("1")
        assert income.amount_ars == Decimal("150000.00")

    def test_usd_income_converts_correctly(self, authenticated_client, user, income_category):
        """Verifica conversiÃ³n correcta de ingreso USD a ARS."""
        create_url = reverse("income:create")
        data = {
            "category": income_category.pk,
            "description": "Freelance USD",
            "amount": "1000.00",
            "currency": Currency.USD,
            "exchange_rate": "1200.00",
            "date": date.today().isoformat(),
        }

        authenticated_client.post(create_url, data)

        income = Income.objects.get(description="Freelance USD")
        assert income.currency == Currency.USD
        assert income.amount_ars == Decimal("1200000.00")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestExchangeRateEdgeCases:
    """Tests de casos lÃ­mite con tipos de cambio."""
