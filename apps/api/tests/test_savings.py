"""Tests para los endpoints de metas de ahorro de la API v1."""

from datetime import date
from decimal import Decimal

import pytest

from apps.savings.models import RolloverSuggestion, RolloverSuggestionStatus, Saving


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.fixture
def saving(user):
    return Saving.objects.create(
        user=user,
        name="Vacaciones",
        target_amount=Decimal("100000.00"),
        currency="ARS",
    )


@pytest.mark.django_db
class TestSavingListEndpoint:
    url = "/api/v1/savings/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_metas_propias(self, client, user, saving):
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_no_muestra_metas_ajenas(self, client, user, other_user):
        Saving.objects.create(
            user=other_user, name="Ajena", target_amount=Decimal("10000.00"), currency="ARS"
        )
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.json()["count"] == 0


@pytest.mark.django_db
class TestSavingCreateEndpoint:
    url = "/api/v1/savings/"

    def test_crear_meta(self, client, user):
        headers = auth_header(client, user)
        data = {"name": "Auto", "target_amount": "500000.00", "currency": "ARS"}
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        assert Saving.objects.filter(name="Auto", user=user).exists()


@pytest.mark.django_db
class TestSavingDepositEndpoint:
    def test_depositar_en_meta(self, client, user, saving):
        headers = auth_header(client, user)
        url = f"/api/v1/savings/{saving.pk}/deposit/"
        response = client.post(
            url,
            {"amount": "10000.00", "description": "Primer depósito"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 200
        saving.refresh_from_db()
        assert saving.current_amount == Decimal("10000.00")

    def test_retirar_de_meta(self, client, user, saving):
        saving.add_deposit(Decimal("50000.00"))
        headers = auth_header(client, user)
        url = f"/api/v1/savings/{saving.pk}/withdraw/"
        response = client.post(
            url,
            {"amount": "10000.00"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 200
        saving.refresh_from_db()
        assert saving.current_amount == Decimal("40000.00")

    def test_no_puede_retirar_mas_de_lo_disponible(self, client, user, saving):
        headers = auth_header(client, user)
        url = f"/api/v1/savings/{saving.pk}/withdraw/"
        response = client.post(
            url,
            {"amount": "999999.00"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 400

    def test_no_puede_depositar_en_meta_ajena(self, client, user, other_user):
        other_saving = Saving.objects.create(
            user=other_user, name="Ajena", target_amount=Decimal("10000.00"), currency="ARS"
        )
        headers = auth_header(client, user)
        url = f"/api/v1/savings/{other_saving.pk}/deposit/"
        response = client.post(
            url, {"amount": "100.00"}, content_type="application/json", **headers
        )
        assert response.status_code == 404


@pytest.fixture
def rollover_suggestion(user):
    return RolloverSuggestion.objects.create(
        user=user,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 2, 1),
        amount=Decimal("1000.00"),
    )


@pytest.mark.django_db
class TestRolloverSuggestionDismissEndpoint:
    def test_descarta_sugerencia(self, client, user, rollover_suggestion):
        headers = auth_header(client, user)
        url = f"/api/v1/rollover-suggestions/{rollover_suggestion.pk}/dismiss/"
        response = client.post(url, **headers)

        assert response.status_code == 200
        rollover_suggestion.refresh_from_db()
        assert rollover_suggestion.status == RolloverSuggestionStatus.DISMISSED

    def test_no_puede_descartar_sugerencia_ajena(self, client, user, other_user):
        other_suggestion = RolloverSuggestion.objects.create(
            user=other_user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("500.00"),
        )
        headers = auth_header(client, user)
        url = f"/api/v1/rollover-suggestions/{other_suggestion.pk}/dismiss/"
        response = client.post(url, **headers)

        assert response.status_code == 404

    def test_no_puede_descartar_sugerencia_ya_resuelta(self, client, user, rollover_suggestion):
        rollover_suggestion.mark_dismissed()
        headers = auth_header(client, user)
        url = f"/api/v1/rollover-suggestions/{rollover_suggestion.pk}/dismiss/"
        response = client.post(url, **headers)

        assert response.status_code == 404


@pytest.mark.django_db
class TestRolloverSuggestionDepositEndpoint:
    def test_destina_sugerencia_a_meta(self, client, user, saving, rollover_suggestion):
        headers = auth_header(client, user)
        url = f"/api/v1/rollover-suggestions/{rollover_suggestion.pk}/deposit/"
        response = client.post(
            url, {"saving_id": saving.pk}, content_type="application/json", **headers
        )

        assert response.status_code == 200
        saving.refresh_from_db()
        rollover_suggestion.refresh_from_db()
        assert saving.current_amount == Decimal("1000.00")
        assert rollover_suggestion.status == RolloverSuggestionStatus.DEPOSITED
        assert rollover_suggestion.saving_id == saving.pk

    def test_deposit_crea_income_compensatorio(self, client, user, saving, rollover_suggestion):
        """DT-067: evita que el balance del período actual quede negativo."""
        from apps.income.models import Income

        headers = auth_header(client, user)
        url = f"/api/v1/rollover-suggestions/{rollover_suggestion.pk}/deposit/"
        client.post(url, {"saving_id": saving.pk}, content_type="application/json", **headers)

        income = Income.objects.get(user=user)
        assert income.amount == Decimal("1000.00")
        assert income.date == date(2026, 1, 31)
        assert income.category.name == "Sobrante de mes anterior"

    def test_no_puede_destinar_a_meta_ajena(self, client, user, other_user, rollover_suggestion):
        other_saving = Saving.objects.create(
            user=other_user, name="Ajena", target_amount=Decimal("10000.00"), currency="ARS"
        )
        headers = auth_header(client, user)
        url = f"/api/v1/rollover-suggestions/{rollover_suggestion.pk}/deposit/"
        response = client.post(
            url, {"saving_id": other_saving.pk}, content_type="application/json", **headers
        )

        assert response.status_code == 404

    def test_no_puede_destinar_sugerencia_ajena(self, client, user, other_user, saving):
        other_suggestion = RolloverSuggestion.objects.create(
            user=other_user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("500.00"),
        )
        headers = auth_header(client, user)
        url = f"/api/v1/rollover-suggestions/{other_suggestion.pk}/deposit/"
        response = client.post(
            url, {"saving_id": saving.pk}, content_type="application/json", **headers
        )

        assert response.status_code == 404
