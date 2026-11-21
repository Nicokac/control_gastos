"""Tests de las sugerencias de gasto fijo en la API v1 (DT-053)."""

from decimal import Decimal

import pytest

from apps.expenses.models import Expense
from apps.recurring.models import DismissedRecurringSuggestion, RecurringExpense
from apps.recurring.tests.test_detection import months_back


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.fixture
def monthly(user, expense_category, today):
    """Un gasto de "Netflix" por mes en los últimos `months` meses del usuario."""

    def _monthly(months=3, owner=None, category=None, description="Netflix"):
        return [
            Expense.objects.create(
                user=owner or user,
                category=category or expense_category,
                date=months_back(today, months - 1 - i),
                description=description,
                amount=Decimal("1000"),
                currency="ARS",
                exchange_rate=Decimal("1"),
            )
            for i in range(months)
        ]

    return _monthly


@pytest.mark.django_db
class TestSuggestionsEndpoint:
    url = "/api/v1/recurring/suggestions/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_las_sugerencias(self, client, user, monthly, expense_category):
        expenses = monthly()

        response = client.get(self.url, **auth_header(client, user))

        assert response.status_code == 200
        assert response.json() == [
            {
                "key": "netflix",
                "name": "Netflix",
                "category": expense_category.pk,
                "category_name": expense_category.name,
                "group_name": expense_category.parent.name,
                "due_day": expenses[-1].date.day,
                "amount": "1000.00",
                "months": 3,
                "expense_count": 3,
            }
        ]

    def test_sin_gastos_repetidos_devuelve_lista_vacia(self, client, user, monthly):
        monthly(months=2)

        assert client.get(self.url, **auth_header(client, user)).json() == []

    def test_no_muestra_las_de_otro_usuario(
        self, client, user, other_user, monthly, expense_category_factory
    ):
        monthly(owner=other_user, category=expense_category_factory(user=other_user))

        assert client.get(self.url, **auth_header(client, user)).json() == []

    def test_consultas_constantes(self, client, user, monthly, django_assert_max_num_queries):
        headers = auth_header(client, user)
        for name in ("Netflix", "Spotify", "Gimnasio", "Internet"):
            monthly(description=name)

        with django_assert_max_num_queries(5):
            assert len(client.get(self.url, **headers).json()) == 4


@pytest.mark.django_db
class TestDismissSuggestionEndpoint:
    url = "/api/v1/recurring/dismiss-suggestion/"

    def test_requiere_autenticacion(self, client):
        assert client.post(self.url, {"suggestion": "netflix"}).status_code == 401

    def test_descarta_y_no_vuelve_a_aparecer(self, client, user, monthly):
        monthly()
        headers = auth_header(client, user)

        response = client.post(
            self.url, {"suggestion": "netflix"}, content_type="application/json", **headers
        )

        assert response.status_code == 204
        assert DismissedRecurringSuggestion.objects.filter(user=user, key="netflix").exists()
        assert client.get("/api/v1/recurring/suggestions/", **headers).json() == []

    def test_dos_veces_no_falla(self, client, user):
        headers = auth_header(client, user)
        for _ in range(2):
            response = client.post(
                self.url, {"suggestion": "netflix"}, content_type="application/json", **headers
            )
            assert response.status_code == 204
        assert DismissedRecurringSuggestion.objects.filter(user=user).count() == 1

    def test_sin_sugerencia_responde_400(self, client, user):
        response = client.post(
            self.url,
            {"suggestion": "  "},
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 400
        assert not DismissedRecurringSuggestion.objects.exists()


@pytest.mark.django_db
class TestCreateFromSuggestion:
    url = "/api/v1/recurring/"

    def payload(self, category, **extra):
        return {"name": "Netflix", "category": category.pk, "due_day": 5, **extra}

    def test_con_sugerencia_vincula_los_pagos(self, client, user, monthly, expense_category, today):
        expenses = monthly()

        response = client.post(
            self.url,
            self.payload(expense_category, suggestion="netflix"),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 201
        assert "suggestion" not in response.json()
        assert response.json()["status"] == "paid"
        recurring = RecurringExpense.objects.get(user=user)
        assert sorted(recurring.expenses.values_list("pk", flat=True)) == [e.pk for e in expenses]

    def test_sin_sugerencia_no_vincula_nada(self, client, user, monthly, expense_category):
        monthly()

        response = client.post(
            self.url,
            self.payload(expense_category),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 201
        assert RecurringExpense.objects.get(user=user).expenses.count() == 0

    def test_no_vincula_pagos_de_otro_usuario(
        self, client, user, other_user, monthly, expense_category, expense_category_factory
    ):
        monthly(owner=other_user, category=expense_category_factory(user=other_user))

        response = client.post(
            self.url,
            self.payload(expense_category, suggestion="netflix"),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 201
        assert not Expense.objects.filter(recurring__isnull=False).exists()

    def test_editar_ignora_la_sugerencia(self, client, user, monthly, expense_category):
        monthly()
        recurring = RecurringExpense.objects.create(
            user=user, name="Otro", category=expense_category, due_day=5
        )

        response = client.put(
            f"{self.url}{recurring.pk}/",
            self.payload(expense_category, suggestion="netflix"),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 200
        assert recurring.expenses.count() == 0
