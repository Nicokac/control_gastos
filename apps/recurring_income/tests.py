"""Tests para el módulo recurring_income (modelos, formularios y vistas)."""

import datetime

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.recurring_income.models import RecurringIncome

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def recurring_income(user, income_category):
    return RecurringIncome.objects.create(
        user=user,
        name="Sueldo",
        category=income_category,
        expected_day=15,
    )


@pytest.fixture
def inactive_recurring_income(user, income_category):
    return RecurringIncome.objects.create(
        user=user,
        name="Freelance",
        category=income_category,
        expected_day=25,
        is_active=False,
    )


# =============================================================================
# TESTS DEL MODELO
# =============================================================================


@pytest.mark.django_db
class TestRecurringIncomeModel:
    def test_str(self, recurring_income):
        assert "Sueldo" in str(recurring_income)
        assert "15" in str(recurring_income)

    def test_last_income_none_when_no_payments(self, recurring_income):
        assert recurring_income.last_income is None

    def test_last_income_returns_most_recent(
        self, recurring_income, user, income_category, income_factory
    ):
        income_factory(
            user, income_category, date=datetime.date(2026, 3, 1), recurring=recurring_income
        )
        newer = income_factory(
            user, income_category, date=datetime.date(2026, 4, 1), recurring=recurring_income
        )
        assert recurring_income.last_income == newer

    def test_is_collected_in_false_when_no_income(self, recurring_income):
        assert recurring_income.is_collected_in(5, 2026) is False

    def test_is_collected_in_true_when_income_exists(
        self, recurring_income, user, income_category, income_factory
    ):
        income_factory(
            user, income_category, date=datetime.date(2026, 5, 10), recurring=recurring_income
        )
        assert recurring_income.is_collected_in(5, 2026) is True

    def test_is_collected_in_false_for_different_month(
        self, recurring_income, user, income_category, income_factory
    ):
        income_factory(
            user, income_category, date=datetime.date(2026, 4, 10), recurring=recurring_income
        )
        assert recurring_income.is_collected_in(5, 2026) is False

    def test_status_collected_when_income_exists(
        self, recurring_income, user, income_category, income_factory
    ):
        income_factory(
            user, income_category, date=datetime.date(2026, 5, 15), recurring=recurring_income
        )
        assert recurring_income.status_for(5, 2026) == "collected"

    def test_status_pending_before_expected_day(self, recurring_income, monkeypatch):
        monkeypatch.setattr(timezone, "localdate", lambda: datetime.date(2026, 5, 10))
        assert recurring_income.status_for(5, 2026) == "pending"

    def test_status_overdue_after_expected_day(self, recurring_income, monkeypatch):
        monkeypatch.setattr(timezone, "localdate", lambda: datetime.date(2026, 5, 20))
        assert recurring_income.status_for(5, 2026) == "overdue"

    def test_status_overdue_for_past_month(self, recurring_income):
        assert recurring_income.status_for(1, 2020) == "overdue"

    def test_status_overdue_for_past_year(self, recurring_income):
        assert recurring_income.status_for(12, 2023) == "overdue"

    def test_status_pending_for_future_month(self, recurring_income, monkeypatch):
        monkeypatch.setattr(timezone, "localdate", lambda: datetime.date(2026, 5, 20))
        assert recurring_income.status_for(6, 2026) == "pending"


# =============================================================================
# TESTS DEL FORMULARIO
# =============================================================================


@pytest.mark.django_db
class TestRecurringIncomeForm:
    def test_form_valid_data(self, user, income_category):
        from apps.recurring_income.forms import RecurringIncomeForm

        form = RecurringIncomeForm(
            data={
                "name": "Sueldo",
                "category": income_category.pk,
                "expected_day": 15,
                "notes": "",
                "is_active": True,
            },
            user=user,
        )
        assert form.is_valid(), form.errors

    def test_form_filters_income_categories(self, user, income_category, expense_category):
        from apps.recurring_income.forms import RecurringIncomeForm

        form = RecurringIncomeForm(user=user)
        qs = form.fields["category"].queryset
        assert income_category in qs
        assert expense_category not in qs

    def test_form_category_has_select_widget_class(self, user):
        from apps.recurring_income.forms import RecurringIncomeForm

        form = RecurringIncomeForm(user=user)
        assert "form-select" in form.fields["category"].widget.attrs.get("class", "")

    def test_form_category_has_empty_label(self, user):
        from apps.recurring_income.forms import RecurringIncomeForm

        form = RecurringIncomeForm(user=user)
        assert form.fields["category"].empty_label is not None

    def test_form_invalid_without_name(self, user, income_category):
        from apps.recurring_income.forms import RecurringIncomeForm

        form = RecurringIncomeForm(
            data={"name": "", "category": income_category.pk, "expected_day": 15},
            user=user,
        )
        assert not form.is_valid()
        assert "name" in form.errors


# =============================================================================
# TESTS DE VISTAS
# =============================================================================


@pytest.mark.django_db
class TestRecurringIncomeListView:
    def test_login_required(self, client):
        url = reverse("recurring_income:list")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response["Location"] or "login" in response["Location"]

    def test_list_shows_active_items(self, authenticated_client, recurring_income):
        url = reverse("recurring_income:list")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert recurring_income in [i["rec"] for i in response.context["items"]]

    def test_list_hides_inactive_by_default(self, authenticated_client, inactive_recurring_income):
        url = reverse("recurring_income:list")
        response = authenticated_client.get(url)
        assert inactive_recurring_income not in [i["rec"] for i in response.context["items"]]

    def test_list_shows_inactive_with_param(self, authenticated_client, inactive_recurring_income):
        url = reverse("recurring_income:list") + "?inactive=1"
        response = authenticated_client.get(url)
        assert inactive_recurring_income in [i["rec"] for i in response.context["items"]]

    def test_context_has_current_month(self, authenticated_client):
        url = reverse("recurring_income:list")
        response = authenticated_client.get(url)
        assert "current_month" in response.context

    def test_context_total_active(
        self, authenticated_client, recurring_income, inactive_recurring_income
    ):
        url = reverse("recurring_income:list")
        response = authenticated_client.get(url)
        assert response.context["total_active"] >= 1

    def test_context_total_collected(self, authenticated_client, recurring_income):
        url = reverse("recurring_income:list")
        response = authenticated_client.get(url)
        assert "total_collected" in response.context

    def test_context_inactive_count(self, authenticated_client, inactive_recurring_income):
        url = reverse("recurring_income:list")
        response = authenticated_client.get(url)
        assert response.context["inactive_count"] >= 1

    def test_user_isolation(self, authenticated_client, other_user, income_category_factory):
        other_cat = income_category_factory(user=other_user)
        RecurringIncome.objects.create(
            user=other_user, name="Otro Ingreso", category=other_cat, expected_day=5
        )
        url = reverse("recurring_income:list")
        response = authenticated_client.get(url)
        names = [i["rec"].name for i in response.context["items"]]
        assert "Otro Ingreso" not in names


@pytest.mark.django_db
class TestRecurringIncomeCreateView:
    def test_login_required(self, client):
        url = reverse("recurring_income:create")
        response = client.get(url)
        assert response.status_code == 302

    def test_get_form(self, authenticated_client):
        url = reverse("recurring_income:create")
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.context["is_edit"] is False

    def test_create_valid(self, authenticated_client, user, income_category):
        url = reverse("recurring_income:create")
        response = authenticated_client.post(
            url,
            {
                "name": "Alquiler cobrado",
                "category": income_category.pk,
                "expected_day": 1,
                "notes": "",
                "is_active": True,
            },
            follow=True,
        )
        assert response.status_code == 200
        assert RecurringIncome.objects.filter(user=user, name="Alquiler cobrado").exists()

    def test_create_assigns_user(self, authenticated_client, user, income_category):
        url = reverse("recurring_income:create")
        authenticated_client.post(
            url,
            {
                "name": "Nuevo",
                "category": income_category.pk,
                "expected_day": 10,
                "notes": "",
                "is_active": True,
            },
        )
        obj = RecurringIncome.objects.get(user=user, name="Nuevo")
        assert obj.user == user

    def test_create_shows_success_message(self, authenticated_client, income_category):
        url = reverse("recurring_income:create")
        response = authenticated_client.post(
            url,
            {
                "name": "Con mensaje",
                "category": income_category.pk,
                "expected_day": 5,
                "notes": "",
                "is_active": True,
            },
            follow=True,
        )
        messages = list(response.context["messages"])
        assert any("creado" in str(m) for m in messages)

    def test_create_invalid_shows_error_message(self, authenticated_client, income_category):
        url = reverse("recurring_income:create")
        response = authenticated_client.post(
            url,
            {"name": "", "category": income_category.pk, "expected_day": 5},
            follow=True,
        )
        messages = list(response.context["messages"])
        assert any("Revisá" in str(m) or "guardar" in str(m) for m in messages)


@pytest.mark.django_db
class TestRecurringIncomeUpdateView:
    def test_login_required(self, client, recurring_income):
        url = reverse("recurring_income:update", kwargs={"pk": recurring_income.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_get_edit_form(self, authenticated_client, recurring_income):
        url = reverse("recurring_income:update", kwargs={"pk": recurring_income.pk})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.context["is_edit"] is True

    def test_update_valid(self, authenticated_client, recurring_income, income_category):
        url = reverse("recurring_income:update", kwargs={"pk": recurring_income.pk})
        response = authenticated_client.post(
            url,
            {
                "name": "Sueldo Actualizado",
                "category": income_category.pk,
                "expected_day": 20,
                "notes": "",
                "is_active": True,
            },
            follow=True,
        )
        assert response.status_code == 200
        recurring_income.refresh_from_db()
        assert recurring_income.name == "Sueldo Actualizado"

    def test_update_shows_success_message(
        self, authenticated_client, recurring_income, income_category
    ):
        url = reverse("recurring_income:update", kwargs={"pk": recurring_income.pk})
        response = authenticated_client.post(
            url,
            {
                "name": "Sueldo Nuevo",
                "category": income_category.pk,
                "expected_day": 15,
                "notes": "",
                "is_active": True,
            },
            follow=True,
        )
        messages = list(response.context["messages"])
        assert any("actualizado" in str(m) for m in messages)

    def test_update_invalid_shows_error_message(
        self, authenticated_client, recurring_income, income_category
    ):
        url = reverse("recurring_income:update", kwargs={"pk": recurring_income.pk})
        response = authenticated_client.post(
            url,
            {"name": "", "category": income_category.pk, "expected_day": 15},
            follow=True,
        )
        messages = list(response.context["messages"])
        assert any("Revisá" in str(m) or "guardar" in str(m) for m in messages)

    def test_other_user_cannot_update(self, other_user_client, recurring_income, income_category):
        url = reverse("recurring_income:update", kwargs={"pk": recurring_income.pk})
        response = other_user_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestRecurringIncomeDeleteView:
    def test_login_required(self, client, recurring_income):
        url = reverse("recurring_income:delete", kwargs={"pk": recurring_income.pk})
        response = client.post(url)
        assert response.status_code == 302

    def test_delete_removes_object(self, authenticated_client, recurring_income):
        pk = recurring_income.pk
        url = reverse("recurring_income:delete", kwargs={"pk": pk})
        authenticated_client.post(url, follow=True)
        assert not RecurringIncome.objects.filter(pk=pk).exists()

    def test_delete_shows_success_message(self, authenticated_client, recurring_income):
        url = reverse("recurring_income:delete", kwargs={"pk": recurring_income.pk})
        response = authenticated_client.post(url, follow=True)
        messages = list(response.context["messages"])
        assert any("eliminado" in str(m) for m in messages)

    def test_other_user_cannot_delete(self, other_user_client, recurring_income):
        url = reverse("recurring_income:delete", kwargs={"pk": recurring_income.pk})
        response = other_user_client.post(url)
        assert response.status_code == 404
        assert RecurringIncome.objects.filter(pk=recurring_income.pk).exists()
