"""Tests para el modelo RecurringExpense."""

from datetime import date

import pytest

from apps.recurring.models import RecurringExpense


@pytest.fixture
def recurring(user, expense_category):
    return RecurringExpense.objects.create(
        user=user,
        name="Edenor",
        category=expense_category,
        due_day=10,
    )


@pytest.mark.django_db
class TestRecurringExpenseModel:
    def test_str(self, recurring):
        assert "Edenor" in str(recurring)
        assert "10" in str(recurring)

    def test_last_expense_none_when_no_payments(self, recurring):
        assert recurring.last_expense is None

    def test_is_paid_in_false_when_no_expenses(self, recurring):
        assert recurring.is_paid_in(5, 2026) is False

    def test_status_pending_before_due_day(self, recurring, monkeypatch):
        import datetime

        from django.utils import timezone

        monkeypatch.setattr(timezone, "localdate", lambda: datetime.date(2026, 5, 5))
        assert recurring.status_for(5, 2026) == "pending"

    def test_status_overdue_after_due_day(self, recurring, monkeypatch):
        import datetime

        from django.utils import timezone

        monkeypatch.setattr(timezone, "localdate", lambda: datetime.date(2026, 5, 15))
        assert recurring.status_for(5, 2026) == "overdue"

    def test_status_paid_when_expense_exists(self, recurring, user, expense_factory):
        expense = expense_factory(user, recurring.category, date=date(2026, 5, 8))
        expense.recurring = recurring
        expense.save()
        assert recurring.status_for(5, 2026) == "paid"

    def test_status_overdue_for_past_month(self, recurring):
        assert recurring.status_for(1, 2020) == "overdue"
