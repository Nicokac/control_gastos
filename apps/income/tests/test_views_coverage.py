"""Tests adicionales de cobertura para income/views.py."""

from datetime import date
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.core.constants import Currency
from apps.income.models import Income
from apps.recurring_income.models import RecurringIncome

# =============================================================================
# IncomeListView — filtros adicionales
# =============================================================================


@pytest.mark.django_db
class TestIncomeListViewFilters:
    """Líneas 61-100: ramas de filtro month-only, year-only, category, amount."""

    def test_filter_month_only(self, authenticated_client, user, income_category, income_factory):
        income_factory(user, income_category, description="Enero", date=date(2025, 1, 5))
        income_factory(user, income_category, description="Febrero", date=date(2025, 2, 5))

        url = reverse("income:list")
        response = authenticated_client.get(url, {"month": "1"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Enero" in content

    def test_filter_year_only(self, authenticated_client, user, income_category, income_factory):
        income_factory(user, income_category, description="2024", date=date(2024, 6, 1))
        income_factory(user, income_category, description="2023", date=date(2023, 6, 1))

        url = reverse("income:list")
        response = authenticated_client.get(url, {"year": "2024"})

        content = response.content.decode()
        assert "2024" in content

    def test_filter_invalid_month_does_not_crash(self, authenticated_client):
        url = reverse("income:list")
        response = authenticated_client.get(url, {"month": "treinta", "year": "2026"})
        assert response.status_code == 200

    def test_filter_invalid_year_does_not_crash(self, authenticated_client):
        url = reverse("income:list")
        response = authenticated_client.get(url, {"year": "abc"})
        assert response.status_code == 200

    def test_filter_category_negative_id_ignored(
        self, authenticated_client, user, income_category, income_factory
    ):
        income_factory(user, income_category, description="Visible", date=timezone.localdate())

        url = reverse("income:list")
        response = authenticated_client.get(url, {"category": "-1"})

        assert response.status_code == 200

    def test_filter_category_invalid_string_ignored(self, authenticated_client):
        url = reverse("income:list")
        response = authenticated_client.get(url, {"category": "nonum"})
        assert response.status_code == 200

    def test_filter_amount_min(self, authenticated_client, user, income_category, income_factory):
        income_factory(
            user,
            income_category,
            description="Bajo",
            amount=Decimal("100.00"),
            date=timezone.localdate(),
        )
        income_factory(
            user,
            income_category,
            description="Alto",
            amount=Decimal("50000.00"),
            date=timezone.localdate(),
        )

        url = reverse("income:list")
        response = authenticated_client.get(url, {"amount_min": "10000"})

        content = response.content.decode()
        assert "Alto" in content
        assert "Bajo" not in content

    def test_filter_amount_max(self, authenticated_client, user, income_category, income_factory):
        income_factory(
            user,
            income_category,
            description="Bajo",
            amount=Decimal("100.00"),
            date=timezone.localdate(),
        )
        income_factory(
            user,
            income_category,
            description="Alto",
            amount=Decimal("50000.00"),
            date=timezone.localdate(),
        )

        url = reverse("income:list")
        response = authenticated_client.get(url, {"amount_max": "500"})

        content = response.content.decode()
        assert "Bajo" in content
        assert "Alto" not in content


# =============================================================================
# IncomeCreateView — flujo desde recurring_income
# =============================================================================


@pytest.mark.django_db
class TestIncomeCreateWithRecurring:
    """Líneas 174, 181-188, 195-202: flujo desde ingreso recurrente."""

    @pytest.fixture
    def recurring_income_obj(self, user, income_category):
        return RecurringIncome.objects.create(
            user=user, name="Sueldo fijo", category=income_category, expected_day=15
        )

    def test_preload_sets_description_and_category(
        self, authenticated_client, recurring_income_obj
    ):
        url = reverse("income:create")
        response = authenticated_client.get(url, {"recurring": recurring_income_obj.pk})

        assert response.status_code == 200
        form = response.context["form"]
        assert form.initial.get("description") == recurring_income_obj.name
        assert form.initial.get("category") == recurring_income_obj.category

    def test_preload_shows_linked_recurring_in_context(
        self, authenticated_client, recurring_income_obj
    ):
        url = reverse("income:create")
        response = authenticated_client.get(url, {"recurring": recurring_income_obj.pk})

        assert response.context.get("linked_recurring") == recurring_income_obj

    def test_preload_invalid_pk_shows_empty_form(self, authenticated_client):
        url = reverse("income:create")
        response = authenticated_client.get(url, {"recurring": 99999})

        assert response.status_code == 200
        assert response.context.get("linked_recurring") is None

    def test_preload_other_user_recurring_ignored(
        self, authenticated_client, other_user, income_category_factory
    ):
        other_cat = income_category_factory(other_user)
        other_rec = RecurringIncome.objects.create(
            user=other_user, name="Ajeno", category=other_cat, expected_day=5
        )
        url = reverse("income:create")
        response = authenticated_client.get(url, {"recurring": other_rec.pk})

        assert response.context.get("linked_recurring") is None

    def test_saving_income_links_recurring_fk(
        self, authenticated_client, user, income_category, recurring_income_obj
    ):
        url = reverse("income:create")
        data = {
            "category": income_category.pk,
            "description": "Sueldo fijo",
            "amount": "100000.00",
            "currency": Currency.ARS,
            "date": timezone.now().date().isoformat(),
        }
        response = authenticated_client.post(url + f"?recurring={recurring_income_obj.pk}", data)

        assert response.status_code == 302
        income = Income.objects.get(description="Sueldo fijo", user=user)
        assert income.recurring == recurring_income_obj

    def test_redirects_to_recurring_income_list_when_recurring_param(
        self, authenticated_client, user, income_category, recurring_income_obj
    ):
        url = reverse("income:create")
        data = {
            "category": income_category.pk,
            "description": "Sueldo via recurrente",
            "amount": "80000.00",
            "currency": Currency.ARS,
            "date": timezone.now().date().isoformat(),
        }
        response = authenticated_client.post(url + f"?recurring={recurring_income_obj.pk}", data)

        assert response.status_code == 302
        assert (
            "recurring_income" in response["Location"] or "recurring-income" in response["Location"]
        )


# =============================================================================
# IncomeCreateView — duplicate y prefill USD
# =============================================================================


@pytest.mark.django_db
class TestIncomeCreateDuplicateAndPrefill:
    """Líneas 203-224: precargar desde duplicate y última cotización USD."""

    def test_duplicate_preloads_data(self, authenticated_client, income):
        url = reverse("income:create")
        response = authenticated_client.get(url, {"duplicate": income.pk})

        assert response.status_code == 200
        form = response.context["form"]
        assert form.initial.get("description") == income.description
        assert form.initial.get("category") == income.category
        assert form.initial.get("amount") == income.amount

    def test_duplicate_invalid_pk_ignored(self, authenticated_client):
        url = reverse("income:create")
        response = authenticated_client.get(url, {"duplicate": 99999})
        assert response.status_code == 200

    def test_duplicate_other_user_income_ignored(
        self, authenticated_client, other_user, income_category_factory, income_factory
    ):
        other_cat = income_category_factory(other_user)
        other_income = income_factory(other_user, other_cat, description="Ajeno")
        url = reverse("income:create")
        response = authenticated_client.get(url, {"duplicate": other_income.pk})

        form = response.context["form"]
        assert form.initial.get("description") != "Ajeno"

    def test_prefills_last_usd_exchange_rate(
        self, authenticated_client, user, income_category, income_factory
    ):
        income_factory(
            user,
            income_category,
            currency="USD",
            exchange_rate=Decimal("1200.00"),
            date=date(2026, 1, 1),
        )

        url = reverse("income:create")
        response = authenticated_client.get(url)

        form = response.context["form"]
        assert form.initial.get("exchange_rate") == Decimal("1200.00")

    def test_no_prefill_when_no_usd_incomes(self, authenticated_client):
        url = reverse("income:create")
        response = authenticated_client.get(url)

        form = response.context["form"]
        assert not form.initial.get("exchange_rate")


# =============================================================================
# IncomeUpdateView — form_invalid
# =============================================================================


@pytest.mark.django_db
class TestIncomeUpdateFormInvalid:
    """Líneas 257-261: form_invalid en update muestra mensaje de error."""

    def test_update_invalid_shows_error_message(self, authenticated_client, income):
        url = reverse("income:update", kwargs={"pk": income.pk})
        response = authenticated_client.post(
            url,
            {
                "category": income.category.pk,
                "description": "",
                "amount": "",
                "currency": income.currency,
                "date": income.date.isoformat(),
            },
            follow=True,
        )

        assert response.status_code == 200
        msgs = [m.message for m in response.context["messages"]]
        assert any("No pudimos guardar el ingreso" in m for m in msgs)
