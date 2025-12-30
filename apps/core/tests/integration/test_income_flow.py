"""
Tests de integración para el flujo completo de ingresos.
"""

from datetime import date
from decimal import Decimal

from django.db import models
from django.urls import reverse

import pytest

from apps.core.constants import Currency
from apps.income.models import Income


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestIncomeCreationFlow:
    """Tests del flujo completo de creación de ingresos."""

    def test_create_income_and_verify_in_list(self, authenticated_client, user, income_category):
        """Verifica que un ingreso creado aparezca en la lista."""
        # 1. Crear ingreso
        create_url = reverse("income:create")
        data = {
            "category": income_category.pk,
            "description": "Sueldo Diciembre",
            "amount": "150000.00",
            "currency": Currency.ARS,
            "date": date.today().isoformat(),
        }

        response = authenticated_client.post(create_url, data)
        assert response.status_code == 302

        # 2. Verificar en DB
        income = Income.objects.get(description="Sueldo Diciembre")
        assert income.user == user
        assert income.amount == Decimal("150000.00")

        # 3. Verificar en lista
        list_url = reverse("income:list")
        response = authenticated_client.get(list_url)

        assert response.status_code == 200
        assert "Sueldo Diciembre" in response.content.decode()

    def test_create_edit_delete_income_flow(self, authenticated_client, user, income_category):
        """Verifica flujo completo: crear -> editar -> eliminar."""
        # 1. CREAR
        create_url = reverse("income:create")
        data = {
            "category": income_category.pk,
            "description": "Ingreso Original",
            "amount": "50000.00",
            "currency": Currency.ARS,
            "date": date.today().isoformat(),
        }

        authenticated_client.post(create_url, data)
        income = Income.objects.get(description="Ingreso Original")

        # 2. EDITAR
        edit_url = reverse("income:update", kwargs={"pk": income.pk})
        data["description"] = "Ingreso Editado"
        data["amount"] = "60000.00"

        response = authenticated_client.post(edit_url, data)
        assert response.status_code == 302

        income.refresh_from_db()
        assert income.description == "Ingreso Editado"
        assert income.amount == Decimal("60000.00")

        # 3. ELIMINAR
        delete_url = reverse("income:delete", kwargs={"pk": income.pk})
        response = authenticated_client.post(delete_url)
        assert response.status_code == 302

        income.refresh_from_db()
        assert income.is_active == False

    def test_income_with_usd_currency_flow(self, authenticated_client, user, income_category):
        """Verifica flujo de ingreso en USD."""
        create_url = reverse("income:create")
        data = {
            "category": income_category.pk,
            "description": "Freelance USD",
            "amount": "500.00",
            "currency": Currency.USD,
            "exchange_rate": "1200.00",
            "date": date.today().isoformat(),
        }

        response = authenticated_client.post(create_url, data)
        assert response.status_code == 302

        income = Income.objects.get(description="Freelance USD")
        assert income.currency == Currency.USD
        assert income.amount_ars == Decimal("600000.00")  # 500 * 1200


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestIncomeBalanceCalculation:
    """Tests de cálculo de balance con ingresos."""

    def test_multiple_incomes_sum_correctly(self, authenticated_client, user, income_category):
        """Verifica que múltiples ingresos sumen correctamente."""
        create_url = reverse("income:create")

        amounts = ["100000.00", "50000.00", "25000.00"]

        for i, amount in enumerate(amounts):
            data = {
                "category": income_category.pk,
                "description": f"Ingreso {i+1}",
                "amount": amount,
                "currency": Currency.ARS,
                "date": date.today().isoformat(),
            }
            authenticated_client.post(create_url, data)

        # Verificar suma total
        total = Income.objects.filter(user=user, is_active=True).aggregate(
            total=models.Sum("amount_ars")
        )["total"]

        assert total == Decimal("175000.00")
