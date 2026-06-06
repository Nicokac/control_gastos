"""Tests para los endpoints de gastos recurrentes de la API v1."""

import pytest

from apps.recurring.models import RecurringExpense


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.fixture
def recurring(user, expense_category):
    return RecurringExpense.objects.create(
        user=user,
        name="Luz",
        category=expense_category,
        due_day=10,
    )


@pytest.mark.django_db
class TestRecurringListEndpoint:
    url = "/api/v1/recurring/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_solo_propios(self, client, user, recurring):
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_no_muestra_ajenos(self, client, user, other_user, expense_category_factory):
        other_cat = expense_category_factory(other_user, name="Otra")
        RecurringExpense.objects.create(
            user=other_user, name="Ajena", category=other_cat, due_day=5
        )
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.json()["count"] == 0


@pytest.mark.django_db
class TestRecurringCreateEndpoint:
    url = "/api/v1/recurring/"

    def test_crear_recurrente(self, client, user, expense_category):
        headers = auth_header(client, user)
        data = {
            "name": "Internet",
            "category": expense_category.pk,
            "due_day": 15,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        assert RecurringExpense.objects.filter(name="Internet", user=user).exists()

    def test_crear_con_cuotas(self, client, user, expense_category):
        headers = auth_header(client, user)
        data = {
            "name": "TV cuotas",
            "category": expense_category.pk,
            "due_day": 10,
            "total_installments": 12,
            "start_date": "2026-01-01",
            "starting_installment": 4,
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        rec = RecurringExpense.objects.get(name="TV cuotas", user=user)
        assert rec.installments_paid == 3


@pytest.mark.django_db
class TestRecurringMarkPaidEndpoint:
    def test_mark_paid_crea_expense(self, client, user, recurring, expense_factory):
        headers = auth_header(client, user)
        url = f"/api/v1/recurring/{recurring.pk}/mark-paid/"
        response = client.post(
            url, {"amount": "5000.00"}, content_type="application/json", **headers
        )
        assert response.status_code == 201
        assert recurring.expenses.count() == 1

    def test_mark_paid_dos_veces_mismo_mes(self, client, user, recurring, expense_factory):
        headers = auth_header(client, user)
        url = f"/api/v1/recurring/{recurring.pk}/mark-paid/"
        client.post(url, {"amount": "5000.00"}, content_type="application/json", **headers)
        response = client.post(
            url, {"amount": "5000.00"}, content_type="application/json", **headers
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestRecurringUnmarkPaidEndpoint:
    def test_unmark_paid_elimina_expense(self, client, user, recurring):
        headers = auth_header(client, user)
        client.post(
            f"/api/v1/recurring/{recurring.pk}/mark-paid/",
            {"amount": "5000.00"},
            content_type="application/json",
            **headers,
        )
        assert recurring.expenses.count() == 1

        response = client.post(
            f"/api/v1/recurring/{recurring.pk}/unmark-paid/",
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 200
        assert recurring.expenses.count() == 0

    def test_unmark_paid_sin_pago_este_mes(self, client, user, recurring):
        headers = auth_header(client, user)
        response = client.post(
            f"/api/v1/recurring/{recurring.pk}/unmark-paid/",
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 400
        assert "No hay pago" in response.json()["detail"]

    def test_unmark_paid_reactiva_cuota_completada(self, client, user, expense_category):
        from datetime import date

        headers = auth_header(client, user)
        rec = RecurringExpense.objects.create(
            user=user,
            name="TV cuotas",
            category=expense_category,
            due_day=10,
            total_installments=1,
            start_date=date.today().replace(day=1),
        )
        client.post(
            f"/api/v1/recurring/{rec.pk}/mark-paid/",
            {"amount": "1000.00"},
            content_type="application/json",
            **headers,
        )
        rec.refresh_from_db()
        assert not rec.is_active

        client.post(
            f"/api/v1/recurring/{rec.pk}/unmark-paid/",
            content_type="application/json",
            **headers,
        )
        rec.refresh_from_db()
        assert rec.is_active

    def test_unmark_paid_no_accede_ajeno(self, client, user, other_user, expense_category_factory):
        other_cat = expense_category_factory(other_user, name="Otra")
        rec = RecurringExpense.objects.create(
            user=other_user, name="Ajena", category=other_cat, due_day=5
        )
        other_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {client.post('/api/v1/auth/token/', {'username': other_user.email, 'password': 'otherpass123'}, content_type='application/json').json()['access']}"  # pragma: allowlist secret
        }
        client.post(
            f"/api/v1/recurring/{rec.pk}/mark-paid/",
            {"amount": "500.00"},
            content_type="application/json",
            **other_headers,
        )

        user_headers = auth_header(client, user)
        response = client.post(
            f"/api/v1/recurring/{rec.pk}/unmark-paid/",
            content_type="application/json",
            **user_headers,
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestRecurringPendingEndpoint:
    def test_pending_retorna_no_pagados(self, client, user, recurring):
        headers = auth_header(client, user)
        response = client.get("/api/v1/recurring/pending/", **headers)
        assert response.status_code == 200
        ids = [r["id"] for r in response.json()]
        assert recurring.pk in ids
