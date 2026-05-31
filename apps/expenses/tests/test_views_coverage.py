"""Tests adicionales de cobertura para expenses/views.py."""

from datetime import date
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest


@pytest.mark.django_db
class TestExpenseListViewYearOnlyFilter:
    """Líneas 91-97: filtro solo por año sin mes."""

    def test_filter_year_only_shows_all_year_expenses(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_factory(user, expense_category, description="Enero año", date=date(2024, 1, 15))
        expense_factory(user, expense_category, description="Julio año", date=date(2024, 7, 15))
        expense_factory(user, expense_category, description="Otro año", date=date(2023, 6, 15))

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"year": "2024"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Enero año" in content
        assert "Julio año" in content
        assert "Otro año" not in content

    def test_filter_invalid_year_does_not_crash(self, authenticated_client):
        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"year": "no-es-año"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestExpenseListViewSubcategoryFilter:
    """Líneas 105-107: filtro por subcategoría específica."""

    def test_filter_by_subcategory(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        cat_a = expense_category_factory(user, name="Sub A")
        cat_b = expense_category_factory(user, name="Sub B")
        expense_factory(user, cat_a, description="Gasto sub A", date=timezone.localdate())
        expense_factory(user, cat_b, description="Gasto sub B", date=timezone.localdate())

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"subcategory": cat_a.pk})

        assert response.status_code == 200
        expenses = list(response.context["expenses"])
        descriptions = [e.description for e in expenses]
        assert "Gasto sub A" in descriptions
        assert "Gasto sub B" not in descriptions


@pytest.mark.django_db
class TestExpenseListViewDailyChart:
    """Líneas 325-354: acumulado diario en contexto."""

    def test_daily_chart_included_when_month_specified(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_factory(
            user,
            expense_category,
            description="d1",
            amount=Decimal("200.00"),
            date=date(2026, 3, 5),
        )
        expense_factory(
            user,
            expense_category,
            description="d2",
            amount=Decimal("300.00"),
            date=date(2026, 3, 15),
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"month": "3", "year": "2026"})

        assert response.status_code == 200
        assert response.context["show_daily_chart"] is True
        assert len(response.context["daily_labels"]) == 31
        assert len(response.context["daily_data"]) == 31

    def test_daily_data_is_cumulative(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_factory(
            user,
            expense_category,
            description="día 1",
            amount=Decimal("100.00"),
            date=date(2026, 5, 1),
        )
        expense_factory(
            user,
            expense_category,
            description="día 2",
            amount=Decimal("200.00"),
            date=date(2026, 5, 2),
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"month": "5", "year": "2026"})

        daily_data = response.context["daily_data"]
        # día 1 acum = 100, día 2 acum = 300
        assert daily_data[0] == 100.0
        assert daily_data[1] == 300.0

    def test_no_daily_chart_when_no_month(self, authenticated_client):
        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"year": "2026"})

        assert response.status_code == 200
        assert response.context.get("show_daily_chart", False) is False


@pytest.mark.django_db
class TestExpenseListViewMonthlyChart:
    """Líneas 358-459: gráfico mensual apilado (solo año sin mes)."""

    def test_monthly_chart_shown_when_year_only(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_factory(
            user,
            expense_category,
            description="ene",
            amount=Decimal("1000.00"),
            date=date(2025, 1, 10),
        )
        expense_factory(
            user,
            expense_category,
            description="jun",
            amount=Decimal("2000.00"),
            date=date(2025, 6, 10),
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"year": "2025"})

        assert response.status_code == 200
        assert response.context["show_monthly_chart"] is True
        assert "monthly_labels" in response.context
        assert len(response.context["monthly_labels"]) == 12
        assert "monthly_datasets" in response.context

    def test_monthly_chart_not_shown_when_month_specified(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_factory(
            user,
            expense_category,
            description="gasto",
            amount=Decimal("500.00"),
            date=date(2025, 3, 10),
        )

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"month": "3", "year": "2025"})

        assert response.context["show_monthly_chart"] is False

    def test_monthly_chart_groups_more_than_6_into_others(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        from apps.categories.models import Category
        from apps.core.constants import CategoryType

        cats = []
        for i in range(8):
            grp = Category.objects.create(
                name=f"Grupo {i}",
                type=CategoryType.EXPENSE,
                user=user,
                parent=None,
                is_system=False,
            )
            sub = expense_category_factory(user, name=f"Sub {i}", parent=grp)
            cats.append(sub)
            expense_factory(
                user,
                sub,
                description=f"g{i}",
                amount=Decimal(f"{(i + 1) * 100}.00"),
                date=date(2025, 1, 10),
            )

        url = reverse("expenses:list")
        response = authenticated_client.get(url, {"year": "2025"})

        assert response.status_code == 200
        assert response.context["show_monthly_chart"] is True
        dataset_labels = [d["label"] for d in response.context["monthly_datasets"]]
        assert "Otros" in dataset_labels


@pytest.mark.django_db
class TestExpenseCreateDuplicate:
    """Líneas 513-525: precargar datos desde un gasto duplicado."""

    def test_duplicate_preloads_data(self, authenticated_client, expense):
        url = reverse("expenses:create")
        response = authenticated_client.get(url, {"duplicate": expense.pk})

        assert response.status_code == 200
        form = response.context["form"]
        assert form.initial.get("description") == expense.description
        assert form.initial.get("category") == expense.category
        assert form.initial.get("amount") == expense.amount

    def test_duplicate_invalid_pk_shows_empty_form(self, authenticated_client):
        url = reverse("expenses:create")
        response = authenticated_client.get(url, {"duplicate": 99999})

        assert response.status_code == 200
        form = response.context["form"]
        assert not form.initial.get("description")

    def test_duplicate_other_user_expense_ignored(
        self, authenticated_client, other_user, expense_category_factory, expense_factory
    ):
        other_cat = expense_category_factory(other_user, name="Ajena")
        other_expense = expense_factory(other_user, other_cat, description="Ajena")

        url = reverse("expenses:create")
        response = authenticated_client.get(url, {"duplicate": other_expense.pk})

        assert response.status_code == 200
        form = response.context["form"]
        assert form.initial.get("description") != "Ajena"


@pytest.mark.django_db
class TestExpenseCreatePrefillUSD:
    """Líneas 528-536: precargar última cotización USD."""

    def test_prefills_last_usd_exchange_rate(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_factory(
            user,
            expense_category,
            currency="USD",
            exchange_rate=Decimal("1200.00"),
            date=date(2026, 1, 1),
        )

        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        form = response.context["form"]
        assert form.initial.get("exchange_rate") == Decimal("1200.00")

    def test_no_prefill_when_no_usd_expenses(self, authenticated_client):
        url = reverse("expenses:create")
        response = authenticated_client.get(url)

        form = response.context["form"]
        assert not form.initial.get("exchange_rate")


@pytest.mark.django_db
class TestExpenseUpdateFormInvalid:
    """Líneas 568-573: form_invalid en update muestra mensaje de error."""

    def test_update_invalid_shows_error_message(self, authenticated_client, expense):
        url = reverse("expenses:update", kwargs={"pk": expense.pk})
        response = authenticated_client.post(
            url,
            {
                "category": expense.category.pk,
                "description": "",
                "amount": "",
                "currency": expense.currency,
                "date": expense.date.isoformat(),
            },
            follow=True,
        )

        assert response.status_code == 200
        msgs = [m.message for m in response.context["messages"]]
        assert any("No pudimos guardar" in m for m in msgs)
