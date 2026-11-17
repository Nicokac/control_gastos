"""Tests para los endpoints de gastos de la API v1."""

from datetime import date

import pytest

from apps.categories.models import CategoryRule
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


@pytest.mark.django_db
class TestExpenseQuickCreateEndpoint:
    """Guardado de la carga rápida desde la app: aprende la regla igual que la web."""

    url = "/api/v1/expenses/quick-create/"

    def _data(self, category, suggested=None, description="Verdulería Don Pepe"):
        return {
            "date": "2026-11-16",
            "description": description,
            "amount": "8500.00",
            "currency": "ARS",
            "exchange_rate": "1",
            "payment_method": "CASH",
            "category": category.pk,
            "suggested_category": suggested.pk if suggested else "",
        }

    def test_crea_el_gasto(self, client, user, expense_category):
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            self._data(expense_category, suggested=expense_category),
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 201
        assert response.json()["description"] == "Verdulería Don Pepe"
        assert Expense.objects.filter(user=user, amount=8500).exists()

    def test_con_la_categoria_sugerida_no_aprende_regla(self, client, user, expense_category):
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            self._data(expense_category, suggested=expense_category),
            content_type="application/json",
            **headers,
        )
        assert response.json()["learned_rule"] is None
        assert not CategoryRule.objects.filter(user=user).exists()

    def test_al_corregir_la_categoria_aprende_la_regla(
        self, client, user, expense_category, expense_category_factory
    ):
        other = expense_category_factory(user, name="Verdulería")
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            self._data(other, suggested=expense_category),
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 201
        assert response.json()["learned_rule"] == {
            "pattern": "verduleria don pepe",
            "category_name": "Verdulería",
        }
        rule = CategoryRule.objects.get(user=user)
        assert (rule.pattern, rule.category) == ("verduleria don pepe", other)

    def test_sin_sugerencia_aprende_la_categoria_elegida(self, client, user, expense_category):
        headers = auth_header(client, user)
        response = client.post(
            self.url, self._data(expense_category), content_type="application/json", **headers
        )
        assert response.json()["learned_rule"]["category_name"] == expense_category.name

    def test_sin_descripcion_no_aprende_regla(self, client, user, expense_category):
        headers = auth_header(client, user)
        response = client.post(
            self.url,
            self._data(expense_category, description=""),
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 201
        assert response.json()["learned_rule"] is None

    def test_no_puede_usar_categoria_ajena(
        self, client, user, other_user, expense_category_factory
    ):
        ajena = expense_category_factory(other_user, name="Ajena")
        headers = auth_header(client, user)
        response = client.post(
            self.url, self._data(ajena), content_type="application/json", **headers
        )
        assert response.status_code == 400
        assert not Expense.objects.filter(user=user).exists()
        assert not CategoryRule.objects.filter(user=user).exists()

    def test_requiere_autenticacion(self, client, expense_category):
        response = client.post(
            self.url, self._data(expense_category), content_type="application/json"
        )
        assert response.status_code == 401
