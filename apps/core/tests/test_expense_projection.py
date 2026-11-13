import datetime
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.core.utils import get_expense_projection
from apps.recurring.models import RecurringExpense

TODAY = datetime.date(2026, 5, 10)


@pytest.fixture
def frozen_today(monkeypatch):
    monkeypatch.setattr(timezone, "localdate", lambda: TODAY)
    return TODAY


@pytest.fixture
def make_recurring(user, expense_category):
    def _make(name="Alquiler", **kwargs):
        return RecurringExpense.objects.create(
            user=user, name=name, category=expense_category, due_day=5, **kwargs
        )

    return _make


@pytest.fixture
def spend(user, expense_category, expense_factory):
    def _spend(amount, day=None, recurring=None, date=None):
        return expense_factory(
            user,
            expense_category,
            amount=Decimal(amount),
            date=date or datetime.date(2026, 5, day),
            recurring=recurring,
        )

    return _spend


@pytest.mark.django_db
class TestExpenseProjection:
    def test_fixed_paid_early_is_not_extrapolated(self, user, frozen_today, make_recurring, spend):
        rent = make_recurring()
        spend("300000", day=5, recurring=rent)
        spend("10000", day=8)

        result = get_expense_projection(user, 5, 2026)

        # 310000 already spent + 10000/10 days * 21 remaining days
        assert result["projection_available"] is True
        assert result["projected_expense"] == Decimal("331000")

    def test_unpaid_fixed_adds_last_payment(self, user, frozen_today, make_recurring, spend):
        internet = make_recurring(name="Internet")
        spend("50000", date=datetime.date(2026, 4, 5), recurring=internet)
        spend("10000", day=8)

        result = get_expense_projection(user, 5, 2026)

        assert result["projected_expense"] == Decimal("10000") + Decimal("21000") + Decimal("50000")

    def test_last_payment_wins_over_estimated_amount(
        self, user, frozen_today, make_recurring, spend
    ):
        internet = make_recurring(name="Internet", estimated_amount=Decimal("99999"))
        spend("50000", date=datetime.date(2026, 4, 5), recurring=internet)
        spend("10000", day=8)

        result = get_expense_projection(user, 5, 2026)

        assert result["projected_expense"] == Decimal("81000")

    def test_never_paid_fixed_uses_estimated_amount(
        self, user, frozen_today, make_recurring, spend
    ):
        make_recurring(name="Gimnasio", estimated_amount=Decimal("20000"))
        make_recurring(name="Sin monto")
        spend("10000", day=8)

        result = get_expense_projection(user, 5, 2026)

        assert result["projected_expense"] == Decimal("10000") + Decimal("21000") + Decimal("20000")

    def test_inactive_and_not_started_fixed_are_ignored(
        self, user, frozen_today, make_recurring, spend
    ):
        make_recurring(name="Viejo", estimated_amount=Decimal("5000"), is_active=False)
        make_recurring(
            name="Cuotas heladera",
            estimated_amount=Decimal("7000"),
            total_installments=6,
            start_date=datetime.date(2026, 6, 1),
        )
        spend("10000", day=8)

        result = get_expense_projection(user, 5, 2026)

        assert result["projected_expense"] == Decimal("31000")

    def test_projected_balance_uses_period_income(
        self, user, frozen_today, spend, income_category, income_factory
    ):
        income_factory(user, income_category, amount=Decimal("100000"), date=TODAY)
        income_factory(
            user, income_category, amount=Decimal("999"), date=datetime.date(2026, 4, 30)
        )
        spend("10000", day=8)

        result = get_expense_projection(user, 5, 2026)

        assert result["projected_balance"] == Decimal("100000") - Decimal("31000")

    def test_financial_period_with_custom_start_day(self, user, monkeypatch, make_recurring, spend):
        user.financial_month_start_day = 10
        user.save(update_fields=["financial_month_start_day"])
        monkeypatch.setattr(timezone, "localdate", lambda: datetime.date(2026, 5, 20))
        rent = make_recurring()
        spend("300000", day=5, recurring=rent)  # previous period: rent still pending in this one
        spend("5000", day=9)  # previous period
        spend("11000", day=15)

        result = get_expense_projection(user, 5, 2026)

        # Period 10/05 to 09/06: 31 days, 11 elapsed, 20 remaining
        assert result["projected_expense"] == Decimal("11000") + Decimal("20000") + Decimal(
            "300000"
        )

    @pytest.mark.parametrize(
        ("today", "month"),
        [
            (datetime.date(2026, 5, 2), 5),  # fewer than 3 days elapsed
            (TODAY, 4),  # not the current period
        ],
    )
    def test_unavailable(self, user, monkeypatch, spend, today, month):
        monkeypatch.setattr(timezone, "localdate", lambda: today)
        spend("10000", day=1)

        result = get_expense_projection(user, month, 2026)

        assert result == {
            "projection_available": False,
            "projected_expense": None,
            "projected_balance": None,
        }

    def test_unavailable_without_expenses(self, user, frozen_today, make_recurring):
        make_recurring(estimated_amount=Decimal("20000"))

        assert get_expense_projection(user, 5, 2026)["projection_available"] is False


@pytest.mark.django_db
class TestProjectionSameOnWebAndApi:
    def test_web_and_api_return_the_same_projection(
        self, client, user, frozen_today, make_recurring, spend, income_category, income_factory
    ):
        user.financial_month_start_day = 3
        user.save(update_fields=["financial_month_start_day"])
        rent = make_recurring()
        spend("300000", day=5, recurring=rent)
        spend("10000", day=1)  # outside the financial period, inside the calendar month
        spend("12000", day=8)
        income_factory(user, income_category, amount=Decimal("500000"), date=TODAY)

        token = client.post(
            "/api/v1/auth/token/",
            {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
            content_type="application/json",
        ).json()["access"]
        api = client.get(
            "/api/v1/dashboard/?month=5&year=2026", HTTP_AUTHORIZATION=f"Bearer {token}"
        ).json()

        client.force_login(user)
        web = client.get(reverse("reports:dashboard")).context

        assert web["projection_available"] is True
        assert Decimal(api["projected_expense"]) == web["projected_expense"]
        assert Decimal(api["projected_balance"]) == web["projected_balance"]
        content = client.get(reverse("reports:dashboard")).content.decode()
        assert 'aria-label="Cómo se calcula la proyección"' in content
