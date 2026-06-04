"""Tests para los endpoints de gastos de la API v1."""

from datetime import date

import pytest

from apps.expenses.models import Expense


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.mark.django_db
class TestExpenseListEndpoint:
    url = "/api/v1/expenses/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_solo_gastos_propios(self, client, user, expense_factory, expense_category):
        expense_factory(user, expense_category, date=date(2026, 6, 1))
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.status_code == 200
        assert response.json()["count"] >= 1

    def test_filtro_por_mes_y_anio(self, client, user, expense_factory, expense_category):
        expense_factory(user, expense_category, date=date(2026, 6, 1))
        expense_factory(user, expense_category, date=date(2026, 5, 1))
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=6&year=2026", **headers)
        assert response.status_code == 200
        dates = [e["date"] for e in response.json()["results"]]
        assert all(d.startswith("2026-06") for d in dates)

    def test_no_muestra_gastos_de_otro_usuario(
        self, client, user, other_user, expense_factory, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        expense_factory(other_user, other_cat, date=date(2026, 6, 1))
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.json()["count"] == 0


@pytest.mark.django_db
class TestExpenseCreateEndpoint:
    url = "/api/v1/expenses/"

    def test_crear_gasto(self, client, user, expense_category):
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Almuerzo",
            "amount": "1500.00",
            "currency": "ARS",
            "category": expense_category.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        assert Expense.objects.filter(description="Almuerzo", user=user).exists()

    def test_monto_negativo_rechazado(self, client, user, expense_category):
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Inválido",
            "amount": "-100.00",
            "currency": "ARS",
            "category": expense_category.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400

    def test_no_puede_usar_categoria_ajena(
        self, client, user, other_user, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Ajena")
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Test",
            "amount": "100.00",
            "currency": "ARS",
            "category": other_cat.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400


@pytest.mark.django_db
class TestExpenseDeleteEndpoint:
    def test_eliminar_gasto_propio(self, client, user, expense_factory, expense_category):
        expense = expense_factory(user, expense_category, date=date(2026, 6, 1))
        headers = auth_header(client, user)
        response = client.delete(f"/api/v1/expenses/{expense.pk}/", **headers)
        assert response.status_code == 204
        assert not Expense.objects.filter(pk=expense.pk).exists()

    def test_no_puede_eliminar_gasto_ajeno(
        self, client, user, other_user, expense_factory, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Otra")
        expense = expense_factory(other_user, other_cat, date=date(2026, 6, 1))
        headers = auth_header(client, user)
        response = client.delete(f"/api/v1/expenses/{expense.pk}/", **headers)
        assert response.status_code == 404
