"""Tests para el endpoint de dashboard de la API v1."""

from datetime import date
from decimal import Decimal

import pytest


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.mark.django_db
class TestDashboardEndpoint:
    url = "/api/v1/dashboard/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_retorna_estructura_correcta(self, client, user):
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=6&year=2026", **headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_expenses" in data
        assert "total_income" in data
        assert "balance" in data
        assert "expenses_by_category" in data
        assert "income_by_category" in data
        assert "savings_progress" in data
        assert "pending_recurring" in data
        assert "recent_transactions" in data

    def test_calcula_totales_correctamente(
        self, client, user, expense_factory, income_factory, expense_category, income_category
    ):
        expense_factory(user, expense_category, date=date(2026, 6, 1), amount=Decimal("1000"))
        expense_factory(user, expense_category, date=date(2026, 6, 15), amount=Decimal("2000"))
        income_factory(user, income_category, date=date(2026, 6, 1), amount=Decimal("10000"))
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=6&year=2026", **headers)
        data = response.json()
        assert Decimal(data["total_expenses"]) == Decimal("3000")
        assert Decimal(data["total_income"]) == Decimal("10000")
        assert Decimal(data["balance"]) == Decimal("7000")

    def test_sin_datos_retorna_ceros(self, client, user):
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=1&year=2020", **headers)
        data = response.json()
        assert Decimal(data["total_expenses"]) == Decimal("0")
        assert Decimal(data["total_income"]) == Decimal("0")

    def test_no_mezcla_datos_de_otros_usuarios(
        self, client, user, other_user, expense_factory, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        expense_factory(other_user, other_cat, date=date(2026, 6, 1), amount=Decimal("9999"))
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=6&year=2026", **headers)
        assert Decimal(response.json()["total_expenses"]) == Decimal("0")
