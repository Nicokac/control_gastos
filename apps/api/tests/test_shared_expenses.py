"""Tests para los endpoints de gastos compartidos de la API v1."""

from datetime import date

import pytest

from apps.shared_expenses.models import HouseholdMember, SharedExpense


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.fixture
def member(user):
    return HouseholdMember.objects.create(user=user, name="María")


@pytest.mark.django_db
class TestHouseholdMemberEndpoint:
    url = "/api/v1/household-members/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_crear_miembro(self, client, user):
        headers = auth_header(client, user)
        response = client.post(
            self.url, {"name": "Juan"}, content_type="application/json", **headers
        )
        assert response.status_code == 201
        assert HouseholdMember.objects.filter(name="Juan", user=user).exists()

    def test_nombre_duplicado_rechazado(self, client, user, member):
        headers = auth_header(client, user)
        response = client.post(
            self.url, {"name": "María"}, content_type="application/json", **headers
        )
        assert response.status_code == 400

    def test_lista_solo_propios(self, client, user, member, other_user):
        HouseholdMember.objects.create(user=other_user, name="Ajeno")
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        names = [m["name"] for m in response.json()["results"]]
        assert "María" in names
        assert "Ajeno" not in names


@pytest.mark.django_db
class TestSharedExpenseEndpoint:
    url = "/api/v1/shared-expenses/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_crear_gasto_compartido(self, client, user, expense_category, member):
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Supermercado",
            "amount": "10000.00",
            "currency": "ARS",
            "category": expense_category.pk,
            "paid_by": member.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        assert SharedExpense.objects.filter(description="Supermercado", user=user).exists()

    def test_crear_sin_pagador(self, client, user, expense_category):
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Luz",
            "amount": "5000.00",
            "currency": "ARS",
            "category": expense_category.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201

    def test_no_puede_usar_miembro_ajeno(self, client, user, expense_category, other_user):
        other_member = HouseholdMember.objects.create(user=other_user, name="Ajeno")
        headers = auth_header(client, user)
        data = {
            "date": "2026-06-01",
            "description": "Test",
            "amount": "1000.00",
            "currency": "ARS",
            "category": expense_category.pk,
            "paid_by": other_member.pk,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400

    def test_filtro_por_mes(self, client, user, expense_category):
        SharedExpense.objects.create(
            user=user,
            date=date(2026, 6, 1),
            description="Junio",
            amount="1000",
            currency="ARS",
            category=expense_category,
        )
        SharedExpense.objects.create(
            user=user,
            date=date(2026, 5, 1),
            description="Mayo",
            amount="1000",
            currency="ARS",
            category=expense_category,
        )
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=6&year=2026", **headers)
        assert response.json()["count"] == 1
