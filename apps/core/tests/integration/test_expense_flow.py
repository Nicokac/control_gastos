"""
Tests de integraciÃ³n para el flujo completo de gastos.
"""

from datetime import date
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.core.constants import Currency
from apps.expenses.models import Expense


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseCreationFlow:
    """Tests del flujo completo de creaciÃ³n de gastos."""

    def test_create_expense_and_verify_in_list(self, authenticated_client, user, expense_category):
        """Verifica que un gasto creado aparezca en la lista."""
        create_url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Compra supermercado",
            "amount": "2500.00",
            "currency": Currency.ARS,
            "date": date.today().isoformat(),
        }

        response = authenticated_client.post(create_url, data)
        assert response.status_code == 302

        expense = Expense.objects.get(description="Compra supermercado")
        assert expense.user == user
        assert expense.amount == Decimal("2500.00")

        list_url = reverse("expenses:list")
        response = authenticated_client.get(list_url)

        assert response.status_code == 200
        assert "Compra supermercado" in response.content.decode()

    def test_create_edit_delete_expense_flow(self, authenticated_client, user, expense_category):
        """Verifica flujo completo: crear -> editar -> eliminar."""
        create_url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Gasto Original",
            "amount": "1000.00",
            "currency": Currency.ARS,
            "date": date.today().isoformat(),
        }

        authenticated_client.post(create_url, data)
        expense = Expense.objects.get(description="Gasto Original")

        edit_url = reverse("expenses:update", kwargs={"pk": expense.pk})
        data["description"] = "Gasto Editado"
        data["amount"] = "1500.00"

        response = authenticated_client.post(edit_url, data)
        assert response.status_code == 302

        expense.refresh_from_db()
        assert expense.description == "Gasto Editado"
        assert expense.amount == Decimal("1500.00")

        delete_url = reverse("expenses:delete", kwargs={"pk": expense.pk})
        response = authenticated_client.post(delete_url)
        assert response.status_code == 302

        assert not Expense.objects.filter(pk=expense.pk).exists()

        list_url = reverse("expenses:list")
        response = authenticated_client.get(list_url)
        assert response.status_code == 200
        assert not Expense.objects.filter(user=user, description="Gasto Editado").exists()

    def test_expense_with_usd_currency_flow(self, authenticated_client, user, expense_category):
        """Verifica flujo de gasto en USD con tipo de cambio."""
        create_url = reverse("expenses:create")
        data = {
            "category": expense_category.pk,
            "description": "Compra Amazon",
            "amount": "50.00",
            "currency": Currency.USD,
            "exchange_rate": "1200.00",
            "date": date.today().isoformat(),
        }

        response = authenticated_client.post(create_url, data)
        assert response.status_code == 302

        expense = Expense.objects.get(description="Compra Amazon")
        assert expense.currency == Currency.USD
        assert expense.amount == Decimal("50.00")
        assert expense.exchange_rate == Decimal("1200.00")
        assert expense.amount_ars == Decimal("60000.00")


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseFilteringFlow:
    """Tests de filtrado de gastos."""

    def test_filter_expenses_by_month(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica filtrado de gastos por mes."""
        expense_factory(user, expense_category, description="Gasto Enero", date=date(2025, 1, 15))
        expense_factory(user, expense_category, description="Gasto Febrero", date=date(2025, 2, 15))

        list_url = reverse("expenses:list")
        response = authenticated_client.get(list_url, {"month": 1, "year": 2025})

        content = response.content.decode()
        assert "Gasto Enero" in content
        assert "Gasto Febrero" not in content

    def test_filter_expenses_by_category(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        """Verifica filtrado de gastos por categorÃ­a."""
        cat_comida = expense_category_factory(user, name="Comida")
        cat_transporte = expense_category_factory(user, name="Transporte")

        expense_factory(user, cat_comida, description="Almuerzo")
        expense_factory(user, cat_transporte, description="Uber")

        list_url = reverse("expenses:list")
        response = authenticated_client.get(list_url, {"category": cat_comida.pk})

        content = response.content.decode()
        assert "Almuerzo" in content
        assert "Uber" not in content
