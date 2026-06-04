"""Tests para los endpoints de ingresos de la API v1."""

from datetime import date

import pytest

from apps.income.models import Income


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.mark.django_db
class TestIncomeListEndpoint:
    url = "/api/v1/income/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_solo_ingresos_propios(self, client, user, income_factory, income_category):
        income_factory(user, income_category, date=date(2026, 6, 1))
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.status_code == 200
        assert response.json()["count"] >= 1

    def test_filtro_por_mes_y_anio(self, client, user, income_factory, income_category):
        income_factory(user, income_category, date=date(2026, 6, 1))
        income_factory(user, income_category, date=date(2026, 5, 1))
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=6&year=2026", **headers)
        assert response.status_code == 200
        dates = [e["date"] for e in response.json()["results"]]
        assert all(d.startswith("2026-06") for d in dates)


@pytest.mark.django_db
class TestIncomeCreateEndpoint:
    url = "/api/v1/income/"

    def test_crear_ingreso(self, client, user, income_category):
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Sueldo junio",
            "amount": "150000.00",
            "currency": "ARS",
            "category": income_category.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        assert Income.objects.filter(description="Sueldo junio", user=user).exists()

    def test_no_puede_usar_categoria_ajena(self, client, user, other_user, income_category_factory):
        other_cat = income_category_factory(other_user, name="Ajena")
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Test",
            "amount": "1000.00",
            "currency": "ARS",
            "category": other_cat.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400
