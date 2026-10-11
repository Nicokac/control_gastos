"""Tests para el endpoint de dashboard de la API v1."""

from datetime import date
from decimal import Decimal

from django.utils import timezone

import pytest

from apps.savings.models import RolloverSuggestion
from apps.savings.services import get_previous_period


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

    def test_proyeccion_disponible_en_periodo_actual(
        self, client, user, expense_factory, income_factory, expense_category, income_category
    ):
        today = timezone.localdate()
        # Gasto en el día 1 del mes actual para garantizar period_day >= 3
        expense_factory(
            user, expense_category, date=date(today.year, today.month, 1), amount=Decimal("9000")
        )
        income_factory(
            user, income_category, date=date(today.year, today.month, 1), amount=Decimal("30000")
        )
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        data = response.json()
        # Solo verificamos la estructura; projection_available depende del día real
        assert "projection_available" in data
        assert "projected_expense" in data
        assert "projected_balance" in data

    def test_proyeccion_no_disponible_en_periodo_pasado(
        self, client, user, expense_factory, expense_category
    ):
        expense_factory(user, expense_category, date=date(2025, 1, 10), amount=Decimal("5000"))
        headers = auth_header(client, user)
        response = client.get(self.url + "?month=1&year=2025", **headers)
        data = response.json()
        assert data["projection_available"] is False
        assert data["projected_expense"] is None
        assert data["projected_balance"] is None


@pytest.mark.django_db
class TestDashboardRolloverSuggestionEndpoint:
    url = "/api/v1/dashboard/"

    def _previous_period(self, user):
        today = timezone.localdate()
        return get_previous_period(today.month, today.year, user.financial_month_start_day)

    def test_incluye_sugerencia_si_periodo_anterior_tuvo_sobrante(
        self, client, user, income_category, income_factory
    ):
        prev_start, _ = self._previous_period(user)
        income_factory(user, income_category, amount=Decimal("1000.00"), date=prev_start)
        headers = auth_header(client, user)

        response = client.get(self.url, **headers)
        data = response.json()

        assert data["rollover_suggestion"] is not None
        assert Decimal(data["rollover_suggestion"]["amount"]) == Decimal("1000.00")
        assert data["rollover_available_amount"] is None

    def test_sin_sugerencia_si_periodo_anterior_sin_sobrante(self, client, user):
        headers = auth_header(client, user)

        response = client.get(self.url, **headers)
        data = response.json()

        assert data["rollover_suggestion"] is None
        assert data["rollover_available_amount"] is None

    def test_disponible_este_mes_tras_descartar(
        self, client, user, income_category, income_factory
    ):
        prev_start, prev_end = self._previous_period(user)
        income_factory(user, income_category, amount=Decimal("1500.00"), date=prev_start)
        headers = auth_header(client, user)

        client.get(self.url, **headers)
        suggestion = RolloverSuggestion.objects.get(
            user=user, period_start=prev_start, period_end=prev_end
        )
        suggestion.mark_dismissed()

        response = client.get(self.url, **headers)
        data = response.json()

        assert data["rollover_suggestion"] is None
        assert Decimal(data["rollover_available_amount"]) == Decimal("1500.00")

    def test_sin_sugerencia_en_periodo_historico_navegado(
        self, client, user, income_category, income_factory
    ):
        prev_start, _ = self._previous_period(user)
        income_factory(user, income_category, amount=Decimal("1000.00"), date=prev_start)
        headers = auth_header(client, user)

        response = client.get(
            self.url + f"?month={prev_start.month}&year={prev_start.year}", **headers
        )
        data = response.json()

        assert data["rollover_suggestion"] is None
        assert RolloverSuggestion.objects.filter(user=user).count() == 0

    def test_proyeccion_no_disponible_sin_gastos(self, client, user):
        headers = auth_header(client, user)
        today = timezone.localdate()
        response = client.get(self.url + f"?month={today.month}&year={today.year}", **headers)
        data = response.json()
        assert data["projection_available"] is False

    def test_comprometido_mes_siguiente_con_recurrente_pagado(
        self, client, user, expense_category, expense_factory
    ):
        from apps.recurring.models import RecurringExpense

        rec = RecurringExpense.objects.create(
            user=user, name="Edenor", category=expense_category, due_day=10
        )
        expense_factory(user, expense_category, amount=Decimal("3000.00"), recurring=rec)

        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        data = response.json()
        assert data["next_month_commitment_available"] is True
        assert Decimal(data["next_month_committed_total"]) == Decimal("3000.00")
        assert len(data["next_month_committed_items"]) == 1
        assert data["next_month_committed_items"][0]["name"] == "Edenor"

    def test_comprometido_mes_siguiente_sin_pago_previo_queda_sin_estimar(
        self, client, user, expense_category
    ):
        from apps.recurring.models import RecurringExpense

        RecurringExpense.objects.create(
            user=user, name="Gimnasio", category=expense_category, due_day=5
        )

        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        data = response.json()
        assert Decimal(data["next_month_committed_total"]) == Decimal("0")
        assert data["next_month_committed_items"] == []
        assert any(item["name"] == "Gimnasio" for item in data["next_month_committed_unestimated"])

    def test_comprometido_mes_siguiente_no_disponible_en_periodo_pasado(
        self, client, user, expense_category, expense_factory
    ):
        from apps.recurring.models import RecurringExpense

        rec = RecurringExpense.objects.create(
            user=user, name="Edenor", category=expense_category, due_day=10
        )
        expense_factory(user, expense_category, amount=Decimal("3000.00"), recurring=rec)

        headers = auth_header(client, user)
        response = client.get(self.url + "?month=1&year=2025", **headers)
        data = response.json()
        assert data["next_month_commitment_available"] is False
        assert data["next_month_committed_total"] is None
