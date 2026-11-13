import datetime
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.core.constants import Currency, PaymentMethod
from apps.expenses.models import Expense
from apps.expenses.quick_entry import QuickEntryError, parse_quick_expense

TODAY = datetime.date(2026, 11, 13)


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(timezone, "localdate", lambda: TODAY)


@pytest.fixture
def supermarket(user, expense_category_factory):
    return expense_category_factory(user=user, name="Supermercado", color="#28a745")


@pytest.mark.django_db
class TestParseAmount:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("15000 super", Decimal("15000")),
            ("15.000 super", Decimal("15000")),
            ("1.250.000 auto", Decimal("1250000")),
            ("15.000,50 super", Decimal("15000.50")),
            ("1500,5 super", Decimal("1500.5")),
            ("1500.50 super", Decimal("1500.50")),
            ("15k super", Decimal("15000")),
            ("1,5k super", Decimal("1500")),
            ("$8.500 nafta", Decimal("8500")),
        ],
    )
    def test_argentine_formats(self, user, text, expected):
        assert parse_quick_expense(user, text).amount == expected

    def test_amount_marked_with_dollar_sign_wins(self, user):
        parsed = parse_quick_expense(user, "$500 2 cafés")

        assert parsed.amount == Decimal("500")
        assert parsed.description == "2 cafés"

    def test_largest_number_is_the_amount_and_others_stay_in_order(self, user):
        parsed = parse_quick_expense(user, "netflix 4 pantallas 8000")

        assert parsed.amount == Decimal("8000")
        assert parsed.description == "netflix 4 pantallas"

    @pytest.mark.parametrize(
        ("text", "message"),
        [
            ("", "Escribí el gasto"),
            ("   ", "Escribí el gasto"),
            ("super débito", "No encontré el monto"),
            ("0 super", "mayor a cero"),
            ("1 " + "a" * 200, "muy largo"),
        ],
    )
    def test_errors(self, user, text, message):
        with pytest.raises(QuickEntryError, match=message):
            parse_quick_expense(user, text)


@pytest.mark.django_db
class TestParseOtherFields:
    @pytest.mark.parametrize(
        ("word", "method"),
        [
            ("débito", PaymentMethod.DEBIT),
            ("DEBITO", PaymentMethod.DEBIT),
            ("crédito", PaymentMethod.CREDIT),
            ("tarjeta", PaymentMethod.CREDIT),
            ("efectivo", PaymentMethod.CASH),
            ("transf", PaymentMethod.TRANSFER),
        ],
    )
    def test_payment_method(self, user, word, method):
        assert parse_quick_expense(user, f"1000 kiosco {word}").payment_method == method

    def test_without_payment_method_is_empty(self, user):
        assert parse_quick_expense(user, "1000 kiosco").payment_method == ""

    @pytest.mark.parametrize(
        ("word", "expected"),
        [
            ("hoy", TODAY),
            ("ayer", datetime.date(2026, 11, 12)),
            ("anteayer", datetime.date(2026, 11, 11)),
            ("12/11", datetime.date(2026, 11, 12)),
            ("1/3/2025", datetime.date(2025, 3, 1)),
            ("20/12", datetime.date(2025, 12, 20)),  # a future day without year means last year
        ],
    )
    def test_dates(self, user, word, expected):
        assert parse_quick_expense(user, f"1000 kiosco {word}").date == expected

    def test_invalid_date_stays_in_description(self, user):
        parsed = parse_quick_expense(user, "1000 kiosco 31/02")

        assert parsed.date == TODAY
        assert parsed.description == "kiosco 31/02"

    def test_stopwords_are_dropped_from_description(self, user):
        parsed = parse_quick_expense(user, "gasté 15000 en el super con débito")

        assert parsed.description == "super"
        assert parsed.payment_method == PaymentMethod.DEBIT

    @pytest.mark.parametrize("text", ["20 usd netflix", "u$s20 netflix", "20 dólares netflix"])
    def test_usd_uses_official_rate(self, user, text):
        with patch("apps.expenses.quick_entry.get_official_usd_rate", return_value=Decimal("1450")):
            parsed = parse_quick_expense(user, text)

        assert parsed.currency == Currency.USD
        assert parsed.amount == Decimal("20")
        assert parsed.exchange_rate == Decimal("1450")
        assert parsed.description == "netflix"

    def test_usd_without_rate_asks_for_full_form(self, user):
        with (
            patch("apps.expenses.quick_entry.get_official_usd_rate", return_value=None),
            pytest.raises(QuickEntryError, match="formulario completo"),
        ):
            parse_quick_expense(user, "20 usd netflix")

    def test_ars_rate_is_one(self, user):
        parsed = parse_quick_expense(user, "1000 kiosco")

        assert parsed.currency == Currency.ARS
        assert parsed.exchange_rate == Decimal("1")


@pytest.mark.django_db
class TestCategorySuggestion:
    def test_uses_own_history(self, user, expense_category, supermarket, expense_factory):
        expense_factory(user, expense_category, description="Super Coto", date=TODAY)
        expense_factory(user, expense_category, description="super chino", date=TODAY)
        expense_factory(user, supermarket, description="super Día", date=TODAY)

        parsed = parse_quick_expense(user, "15000 super")

        assert parsed.category == expense_category
        assert parsed.category_source == "historial"

    def test_ignores_other_users_history(
        self, user, other_user, expense_category_factory, expense_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Cosas")
        expense_factory(other_user, theirs, description="super", date=TODAY)

        parsed = parse_quick_expense(user, "15000 super")

        assert parsed.category is None

    def test_ignores_history_older_than_a_year(self, user, expense_category, expense_factory):
        expense_factory(
            user, expense_category, description="super", date=datetime.date(2025, 10, 1)
        )

        assert parse_quick_expense(user, "15000 super").category is None

    def test_falls_back_to_category_name(self, user, supermarket):
        parsed = parse_quick_expense(user, "15000 super")

        assert parsed.category == supermarket
        assert parsed.category_source == "nombre"

    def test_name_match_ignores_accents(self, user, expense_category_factory):
        pharmacy = expense_category_factory(user=user, name="Farmacía")

        assert parse_quick_expense(user, "3000 farmacia").category == pharmacy

    def test_no_suggestion_without_matches(self, user, supermarket):
        parsed = parse_quick_expense(user, "15000 zzz")

        assert parsed.category is None
        assert parsed.category_source is None


@pytest.mark.django_db
class TestQuickParseView:
    url = reverse("expenses:quick_parse")

    def test_requires_login(self, client):
        response = client.post(self.url, {"text": "1000 kiosco"}, content_type="application/json")

        assert response.status_code == 302

    def test_returns_preview(self, authenticated_client, supermarket):
        response = authenticated_client.post(
            self.url, {"text": "15000 super débito ayer"}, content_type="application/json"
        )

        data = response.json()
        assert response.status_code == 200
        assert data["ok"] is True
        assert data["amount"] == "15000"
        assert data["date"] == "2026-11-12"
        assert data["payment_method"] == PaymentMethod.DEBIT
        assert data["payment_method_display"] == "Tarjeta de Débito"
        assert data["category_id"] == supermarket.pk
        assert "15.000" in data["amount_display"]
        assert data["conversion_display"] == ""

    def test_usd_preview_shows_pesos(self, authenticated_client):
        with patch("apps.expenses.quick_entry.get_official_usd_rate", return_value=Decimal("1500")):
            response = authenticated_client.post(
                self.url, {"text": "20 usd netflix"}, content_type="application/json"
            )

        assert response.json()["conversion_display"] == "≈ $ 30.000,00 (dólar oficial $ 1.500,00)"

    def test_error_returns_400(self, authenticated_client):
        response = authenticated_client.post(
            self.url, {"text": "sin monto"}, content_type="application/json"
        )

        assert response.status_code == 400
        assert response.json() == {"ok": False, "error": response.json()["error"]}

    def test_invalid_body(self, authenticated_client):
        response = authenticated_client.post(self.url, "no json", content_type="application/json")

        assert response.status_code == 400

    def test_get_not_allowed(self, authenticated_client):
        assert authenticated_client.get(self.url).status_code == 405


@pytest.mark.django_db
class TestQuickCreateView:
    url = reverse("expenses:quick_create")

    def data(self, category, **overrides):
        values = {
            "amount": "15000",
            "currency": "ARS",
            "exchange_rate": "1",
            "date": "2026-11-12",
            "payment_method": PaymentMethod.DEBIT,
            "description": "super",
            "category": category.pk,
            "next": reverse("reports:dashboard"),
        }
        values.update(overrides)
        return values

    def test_requires_login(self, client, supermarket):
        response = client.post(self.url, self.data(supermarket))

        assert response.status_code == 302
        assert not Expense.objects.exists()

    def test_creates_expense_and_returns_to_page(self, authenticated_client, user, supermarket):
        response = authenticated_client.post(self.url, self.data(supermarket), follow=True)

        expense = Expense.objects.get()
        assert expense.user == user
        assert expense.amount == Decimal("15000")
        assert expense.category == supermarket
        assert expense.date == datetime.date(2026, 11, 12)
        assert expense.payment_method == PaymentMethod.DEBIT
        assert response.redirect_chain[-1][0] == reverse("reports:dashboard")
        messages = [str(m) for m in response.context["messages"]]
        assert any("Gasto registrado: super" in m for m in messages)

    def test_usd_expense_converts_to_pesos(self, authenticated_client, supermarket):
        authenticated_client.post(
            self.url,
            self.data(supermarket, amount="20", currency="USD", exchange_rate="1450.00"),
        )

        expense = Expense.objects.get()
        assert expense.currency == Currency.USD
        assert expense.amount_ars == Decimal("29000.00")

    def test_rejects_other_users_category(
        self, authenticated_client, other_user, expense_category_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Ajena")

        response = authenticated_client.post(self.url, self.data(theirs), follow=True)

        assert not Expense.objects.exists()
        messages = [str(m) for m in response.context["messages"]]
        assert any("No pudimos guardar el gasto" in m for m in messages)

    def test_missing_category_is_not_saved(self, authenticated_client, supermarket):
        data = self.data(supermarket)
        data["category"] = ""
        authenticated_client.post(self.url, data)

        assert not Expense.objects.exists()

    def test_external_next_falls_back_to_expense_list(self, authenticated_client, supermarket):
        response = authenticated_client.post(
            self.url, self.data(supermarket, next="https://evil.example.com/")
        )

        assert response.url == reverse("expenses:list")


@pytest.mark.django_db
class TestQuickExpenseBarAndFullForm:
    def test_bar_on_expense_list(self, authenticated_client, supermarket):
        content = authenticated_client.get(reverse("expenses:list")).content.decode()

        assert 'id="quickExpense"' in content
        assert f'<option value="{supermarket.pk}">Supermercado</option>' in content

    def test_bar_on_dashboard_only_for_current_period(self, authenticated_client):
        current = authenticated_client.get(reverse("reports:dashboard")).content.decode()
        past = authenticated_client.get(
            reverse("reports:dashboard"), {"month": 1, "year": 2026}
        ).content.decode()

        assert 'id="quickExpense"' in current
        assert 'id="quickExpense"' not in past

    def test_bar_hides_categories_of_other_users(
        self, authenticated_client, other_user, expense_category_factory
    ):
        expense_category_factory(user=other_user, name="Categoría ajena")

        content = authenticated_client.get(reverse("expenses:list")).content.decode()

        assert "Categoría ajena" not in content

    def test_full_form_is_prefilled(self, authenticated_client, supermarket):
        response = authenticated_client.get(
            reverse("expenses:create"),
            {
                "from_quick": "1",
                "amount": "15000",
                "date": "2026-11-12",
                "description": "super",
                "payment_method": PaymentMethod.DEBIT,
                "category": supermarket.pk,
            },
        )

        initial = response.context["form"].initial
        assert initial["amount"] == "15000"
        assert initial["date"] == datetime.date(2026, 11, 12)
        assert 'value="2026-11-12"' in response.content.decode()
        assert initial["description"] == "super"
        assert initial["category"] == supermarket

    def test_full_form_ignores_other_users_category(
        self, authenticated_client, other_user, expense_category_factory
    ):
        theirs = expense_category_factory(user=other_user, name="Ajena")

        response = authenticated_client.get(
            reverse("expenses:create"), {"from_quick": "1", "category": theirs.pk}
        )

        assert "category" not in response.context["form"].initial

    def test_full_form_ignores_invalid_date(self, authenticated_client):
        response = authenticated_client.get(
            reverse("expenses:create"), {"from_quick": "1", "date": "13/11/2026"}
        )

        assert response.status_code == 200
        assert response.context["form"].initial.get("date") != "13/11/2026"


@pytest.mark.django_db
class TestQuickParseApi:
    url = "/api/v1/expenses/quick-parse/"

    def token(self, client, user):
        response = client.post(
            "/api/v1/auth/token/",
            {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
            content_type="application/json",
        )
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}

    def test_requires_authentication(self, client):
        response = client.post(self.url, {"text": "1000 kiosco"}, content_type="application/json")

        assert response.status_code == 401

    def test_returns_preview(self, client, user, supermarket):
        response = client.post(
            self.url,
            {"text": "15000 super efectivo"},
            content_type="application/json",
            **self.token(client, user),
        )

        data = response.json()
        assert response.status_code == 200
        assert data["category_id"] == supermarket.pk
        assert data["payment_method"] == PaymentMethod.CASH

    def test_error_returns_400(self, client, user):
        response = client.post(
            self.url, {"text": "nada"}, content_type="application/json", **self.token(client, user)
        )

        assert response.status_code == 400
        assert response.json()["ok"] is False
