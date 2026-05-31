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

    # --- installments ---

    def test_is_installment_false_without_total(self, recurring):
        assert recurring.is_installment is False

    def test_is_installment_true_with_total(self, user, expense_category):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Cuotas TV",
            category=expense_category,
            due_day=5,
            total_installments=12,
            start_date=date(2026, 1, 1),
        )
        assert rec.is_installment is True

    def test_installments_paid_none_without_total(self, recurring):
        assert recurring.installments_paid is None

    def test_installments_paid_none_without_start_date(self, user, expense_category):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Cuotas sin fecha",
            category=expense_category,
            due_day=5,
            total_installments=6,
        )
        assert rec.installments_paid is None

    def test_installments_paid_counts_expenses(self, user, expense_category, expense_factory):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Cuotas Netflix",
            category=expense_category,
            due_day=5,
            total_installments=12,
            start_date=date(2026, 1, 1),
        )
        exp = expense_factory(user, expense_category, date=date(2026, 2, 5))
        exp.recurring = rec
        exp.save()
        assert rec.installments_paid == 1

    def test_installments_remaining_none_without_total(self, recurring):
        assert recurring.installments_remaining is None

    def test_installments_remaining_counts_down(self, user, expense_category, expense_factory):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Cuotas Gym",
            category=expense_category,
            due_day=1,
            total_installments=3,
            start_date=date(2026, 1, 1),
        )
        exp = expense_factory(user, expense_category, date=date(2026, 1, 1))
        exp.recurring = rec
        exp.save()
        assert rec.installments_remaining == 2

    def test_installments_remaining_not_negative(self, user, expense_category, expense_factory):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Cuotas Extra",
            category=expense_category,
            due_day=1,
            total_installments=1,
            start_date=date(2026, 1, 1),
        )
        for i in range(3):
            exp = expense_factory(user, expense_category, date=date(2026, i + 1, 1))
            exp.recurring = rec
            exp.save()
        assert rec.installments_remaining == 0

    # --- auto_deactivate_if_complete ---

    def test_auto_deactivate_does_nothing_without_installments(self, recurring):
        recurring.auto_deactivate_if_complete()
        recurring.refresh_from_db()
        assert recurring.is_active is True

    def test_auto_deactivate_does_nothing_if_already_inactive(self, user, expense_category):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Ya inactivo",
            category=expense_category,
            due_day=1,
            total_installments=1,
            start_date=date(2026, 1, 1),
            is_active=False,
        )
        rec.auto_deactivate_if_complete()
        rec.refresh_from_db()
        assert rec.is_active is False

    def test_auto_deactivate_deactivates_when_complete(
        self, user, expense_category, expense_factory
    ):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Cuota final",
            category=expense_category,
            due_day=1,
            total_installments=1,
            start_date=date(2026, 1, 1),
        )
        exp = expense_factory(user, expense_category, date=date(2026, 1, 1))
        exp.recurring = rec
        exp.save()
        rec.auto_deactivate_if_complete()
        rec.refresh_from_db()
        assert rec.is_active is False

    def test_auto_deactivate_keeps_active_when_incomplete(
        self, user, expense_category, expense_factory
    ):
        rec = RecurringExpense.objects.create(
            user=user,
            name="Cuotas pendientes",
            category=expense_category,
            due_day=1,
            total_installments=3,
            start_date=date(2026, 1, 1),
        )
        exp = expense_factory(user, expense_category, date=date(2026, 1, 1))
        exp.recurring = rec
        exp.save()
        rec.auto_deactivate_if_complete()
        rec.refresh_from_db()
        assert rec.is_active is True
