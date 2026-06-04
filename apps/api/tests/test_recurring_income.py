"""Tests para los endpoints de ingresos recurrentes de la API v1."""

import pytest

from apps.recurring_income.models import RecurringIncome


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.fixture
def recurring_income(user, income_category):
    return RecurringIncome.objects.create(
        user=user,
        name="Sueldo",
        category=income_category,
        expected_day=25,
    )


@pytest.mark.django_db
class TestRecurringIncomeListEndpoint:
    url = "/api/v1/recurring-income/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_solo_propios(self, client, user, recurring_income):
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.status_code == 200
        assert response.json()["count"] == 1


@pytest.mark.django_db
class TestRecurringIncomeCreateEndpoint:
    url = "/api/v1/recurring-income/"

    def test_crear_recurrente(self, client, user, income_category):
        headers = auth_header(client, user)
        data = {
            "name": "Alquiler cobrado",
            "category": income_category.pk,
            "expected_day": 1,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        assert RecurringIncome.objects.filter(name="Alquiler cobrado", user=user).exists()


@pytest.mark.django_db
class TestRecurringIncomeMarkReceivedEndpoint:
    def test_mark_received_crea_income(self, client, user, recurring_income):
        headers = auth_header(client, user)
        url = f"/api/v1/recurring-income/{recurring_income.pk}/mark-received/"
        response = client.post(
            url, {"amount": "150000.00"}, content_type="application/json", **headers
        )
        assert response.status_code == 201
        assert recurring_income.incomes.count() == 1

    def test_mark_received_dos_veces_mismo_mes(self, client, user, recurring_income):
        headers = auth_header(client, user)
        url = f"/api/v1/recurring-income/{recurring_income.pk}/mark-received/"
        client.post(url, {"amount": "150000.00"}, content_type="application/json", **headers)
        response = client.post(
            url, {"amount": "150000.00"}, content_type="application/json", **headers
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestRecurringIncomePendingEndpoint:
    def test_pending_retorna_no_cobrados(self, client, user, recurring_income):
        headers = auth_header(client, user)
        response = client.get("/api/v1/recurring-income/pending/", **headers)
        assert response.status_code == 200
        ids = [r["id"] for r in response.json()]
        assert recurring_income.pk in ids
