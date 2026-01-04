"""
Tests para las vistas de Budget.
"""

from decimal import Decimal

from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone

import pytest

from apps.budgets.models import Budget


@pytest.mark.django_db
class TestBudgetListView:
    """Tests para la vista de listado de presupuestos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("budgets:list")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_list_user_budgets(self, authenticated_client, budget):
        """Verifica que liste los presupuestos del usuario."""
        url = reverse("budgets:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200

    def test_excludes_other_user_budgets(
        self, authenticated_client, other_user, expense_category_factory, budget_factory
    ):
        """Verifica que no muestre presupuestos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        budget_factory(other_user, other_cat)

        url = reverse("budgets:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200

    def test_filter_by_month_year(self, authenticated_client, budget):
        """Verifica filtrado por mes/año."""
        url = reverse("budgets:list")
        response = authenticated_client.get(url, {"month": budget.month, "year": budget.year})

        assert response.status_code == 200

    def test_defaults_to_current_month_when_no_params(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """
        Cubre branch:
        - if not month and not year -> toma timezone.now()
        """
        today = timezone.now().date()
        b_current = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("100.00")
        )
        other_month = 1 if today.month != 1 else 2
        b_other = budget_factory(
            user, expense_category, month=other_month, year=today.year, amount=Decimal("200.00")
        )

        url = reverse("budgets:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        budgets = list(response.context["budgets"])
        assert b_current in budgets
        assert b_other not in budgets

    def test_invalid_month_year_are_sanitized_and_dont_crash(
        self, authenticated_client, monkeypatch
    ):
        """
        Cubre branches:
        - month fuera de rango => month=None
        - year fuera de rango => year=None
        - ValueError/TypeError => month/year None
        y valida que get_with_spent reciba los valores sanitizados.
        """
        captured = {}

        def fake_get_with_spent(*, user, month, year):
            captured["month"] = month
            captured["year"] = year
            return Budget.objects.none()

        monkeypatch.setattr(Budget, "get_with_spent", staticmethod(fake_get_with_spent))

        url = reverse("budgets:list")

        r1 = authenticated_client.get(url, {"month": 13, "year": 9999})
        assert r1.status_code == 200
        assert captured["month"] is None
        assert captured["year"] is None

        r2 = authenticated_client.get(url, {"month": "abc", "year": "def"})
        assert r2.status_code == 200
        assert captured["month"] is None
        assert captured["year"] is None

    def test_category_filter_valid_and_invalid(
        self, authenticated_client, user, expense_category_factory, budget_factory
    ):
        """
        Cubre:
        - filtro category OK (int) aplica filter(category_id=...)
        - category inválido (no int) no rompe
        """
        cat1 = expense_category_factory(user, name="Cat 1")
        cat2 = expense_category_factory(user, name="Cat 2")
        b1 = budget_factory(user, cat1, amount=Decimal("100.00"))
        b2 = budget_factory(user, cat2, amount=Decimal("200.00"))

        url = reverse("budgets:list")

        resp_ok = authenticated_client.get(url, {"category": str(cat1.id)})
        assert resp_ok.status_code == 200
        budgets_ok = list(resp_ok.context["budgets"])
        assert b1 in budgets_ok
        assert b2 not in budgets_ok

        resp_bad = authenticated_client.get(url, {"category": "not-an-int"})
        assert resp_bad.status_code == 200

    def test_context_includes_summary_and_period_name(self, rf, user, monkeypatch):
        """
        Cubre get_context_data:
        - summary (total_budgeted, total_spent, remaining, % y counts)
        - period_name
        Sin renderizar template.
        """
        from django.utils import timezone

        from apps.budgets.views import BudgetListView

        today = timezone.now().date()

        class DummyBudget:
            def __init__(self, amount, spent_amount, is_over_budget, is_near_limit):
                self.amount = Decimal(amount)
                self.spent_amount = Decimal(spent_amount)
                self.is_over_budget = is_over_budget
                self.is_near_limit = is_near_limit

        dummy_qs = [
            DummyBudget("100.00", "80.00", False, True),
            DummyBudget("50.00", "60.00", True, False),
        ]

        def fake_get_with_spent(*, user, month, year):
            return dummy_qs

        monkeypatch.setattr(
            Budget,
            "get_with_spent",
            staticmethod(fake_get_with_spent),
        )

        request = rf.get(
            reverse("budgets:list"),
            {"month": today.month, "year": today.year},
        )
        request.user = user

        view = BudgetListView()
        view.request = request
        view.args = ()
        view.kwargs = {}

        queryset = view.get_queryset()
        context = view.get_context_data(object_list=queryset)

        summary = context["summary"]

        assert summary["total_budgeted"] == Decimal("150.00")
        assert summary["total_spent"] == Decimal("140.00")
        assert summary["total_remaining"] == Decimal("10.00")
        assert summary["budget_count"] == 2
        assert summary["over_budget_count"] == 1
        assert summary["warning_count"] == 1

        assert "period_name" in context
        assert str(today.year) in context["period_name"]


@pytest.mark.django_db
class TestBudgetCreateView:
    """Tests para la vista de creación de presupuestos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("budgets:create")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_create_form(self, authenticated_client):
        """Verifica que muestre el formulario de creación."""
        url = reverse("budgets:create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        # cobertura extra de contexto
        assert response.context.get("is_edit") is False

    def test_create_budget_success(self, authenticated_client, user, expense_category):
        """Verifica creación exitosa de presupuesto."""
        today = timezone.now().date()

        if today.month == 12:
            test_month = 1
            test_year = today.year + 1
        else:
            test_month = today.month + 1
            test_year = today.year

        url = reverse("budgets:create")
        data = {
            "category": expense_category.pk,
            "month": test_month,
            "year": test_year,
            "amount": "50000.00",
            "alert_threshold": 80,
        }

        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        assert Budget.objects.filter(
            category=expense_category, month=test_month, year=test_year, user=user
        ).exists()

        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("creado correctamente" in m for m in msgs)

    def test_budget_assigned_to_current_user(self, authenticated_client, user, expense_category):
        """Verifica que el presupuesto se asigne al usuario actual."""
        today = timezone.now().date()

        if today.month == 1:
            test_month = 12
            test_year = today.year - 1
        else:
            test_month = today.month - 1
            test_year = today.year

        url = reverse("budgets:create")
        data = {
            "category": expense_category.pk,
            "month": test_month,
            "year": test_year,
            "amount": "30000.00",
            "alert_threshold": 75,
        }

        authenticated_client.post(url, data)

        budget = Budget.objects.get(month=test_month, year=test_year, category=expense_category)
        assert budget.user == user

    def test_duplicate_budget_rejected(self, authenticated_client, budget):
        """Verifica que rechace presupuesto duplicado."""
        url = reverse("budgets:create")
        data = {
            "category": budget.category.pk,
            "month": budget.month,
            "year": budget.year,
            "amount": "60000.00",
            "alert_threshold": 80,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 200
        assert response.context["form"].errors

    def test_create_budget_invalid_shows_error_message(
        self, authenticated_client, expense_category
    ):
        """
        Cubre BudgetCreateView.form_invalid() + messages.error(...)
        """
        url = reverse("budgets:create")
        data = {
            "category": expense_category.pk,
            "month": timezone.now().date().month,
            "year": timezone.now().date().year,
            "amount": "",  # inválido
            "alert_threshold": 80,
        }

        response = authenticated_client.post(url, data, follow=True)
        assert response.status_code == 200
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("Corregí los errores del formulario" in m for m in msgs)


@pytest.mark.django_db
class TestBudgetUpdateView:
    """Tests para la vista de edición de presupuestos."""

    def test_login_required(self, client, budget):
        """Verifica que requiera autenticación."""
        url = reverse("budgets:update", kwargs={"pk": budget.pk})
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_update_form(self, authenticated_client, budget):
        """Verifica que muestre el formulario de edición."""
        url = reverse("budgets:update", kwargs={"pk": budget.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context.get("is_edit") is True

    def test_update_budget_success(self, authenticated_client, budget):
        """Verifica edición exitosa de presupuesto."""
        url = reverse("budgets:update", kwargs={"pk": budget.pk})
        data = {
            "category": budget.category.pk,
            "month": budget.month,
            "year": budget.year,
            "amount": "100000.00",
            "alert_threshold": 90,
            "notes": budget.notes or "",
        }

        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200

        budget.refresh_from_db()
        assert budget.amount == Decimal("100000.00")
        assert budget.alert_threshold == 90

        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("actualizado correctamente" in m for m in msgs)

    def test_cannot_update_other_user_budget(
        self, authenticated_client, other_user, expense_category_factory, budget_factory
    ):
        """Verifica que no pueda editar presupuestos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_budget = budget_factory(other_user, other_cat)

        url = reverse("budgets:update", kwargs={"pk": other_budget.pk})
        response = authenticated_client.get(url)

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestBudgetDeleteView:
    """Tests para la vista de eliminación de presupuestos."""

    def test_login_required(self, client, budget):
        """Verifica que requiera autenticación."""
        url = reverse("budgets:delete", kwargs={"pk": budget.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_delete_budget_success(self, authenticated_client, budget):
        """Verifica eliminación exitosa de presupuesto."""
        url = reverse("budgets:delete", kwargs={"pk": budget.pk})

        response = authenticated_client.post(url, follow=True)

        assert response.status_code == 200

        budget.refresh_from_db()
        assert not budget.is_active

        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("eliminado correctamente" in m for m in msgs)

    def test_cannot_delete_other_user_budget(
        self, authenticated_client, other_user, expense_category_factory, budget_factory
    ):
        """Verifica que no pueda eliminar presupuestos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_budget = budget_factory(other_user, other_cat)

        url = reverse("budgets:delete", kwargs={"pk": other_budget.pk})
        response = authenticated_client.post(url)

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestBudgetDetailView:
    def test_detail_no_last_year_budget(
        self, authenticated_client, user, expense_category, budget_factory, expense_factory
    ):
        """
        Cubre:
        - expenses del período ([:10])
        - except Budget.DoesNotExist => last_year_budget None, year_comparison None
        """
        today = timezone.now().date()
        budget = budget_factory(user, expense_category, month=today.month, year=today.year)

        for i in range(12):
            expense_factory(
                user,
                expense_category,
                date=today.replace(day=1),
                description=f"gasto {i}",
                amount=Decimal("10.00"),
            )

        other_month = 1 if today.month != 1 else 2
        expense_factory(
            user,
            expense_category,
            date=today.replace(month=other_month, day=1),
            description="fuera de periodo",
            amount=Decimal("999.00"),
        )

        url = reverse("budgets:detail", kwargs={"pk": budget.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        expenses = list(response.context["expenses"])
        assert len(expenses) == 10
        assert response.context["last_year_budget"] is None
        assert response.context["year_comparison"] is None

    def test_detail_with_last_year_budget(
        self, authenticated_client, user, expense_category, budget_factory, expense_factory
    ):
        """
        Cubre:
        - try Budget.objects.get(... year-1 ...)
        - year_comparison calculado (percentage_change, flags)
        """
        today = timezone.now().date()
        current = budget_factory(user, expense_category, month=today.month, year=today.year)

        expense_factory(
            user,
            expense_category,
            date=today.replace(day=1),
            description="actual",
            amount=Decimal("50.00"),
        )

        last_year = budget_factory(user, expense_category, month=today.month, year=today.year - 1)

        expense_factory(
            user,
            expense_category,
            date=today.replace(year=today.year - 1, day=1),
            description="año pasado",
            amount=Decimal("20.00"),
        )

        url = reverse("budgets:detail", kwargs={"pk": current.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["last_year_budget"].pk == last_year.pk
        comparison = response.context["year_comparison"]
        assert comparison is not None
        assert "percentage_change" in comparison


@pytest.mark.django_db
class TestCopyBudgetsView:
    def test_copy_login_required(self, client):
        url = reverse("budgets:copy")
        response = client.get(url)
        assert response.status_code == 302
        assert "login" in response.url

    def test_copy_warns_when_no_source_budgets(self, authenticated_client):
        """
        Cubre:
        source_budgets.exists() == False
        """
        url = reverse("budgets:copy")
        today = timezone.now().date()

        response = authenticated_client.post(
            url,
            {"target_month": today.month, "target_year": today.year},
            follow=True,
        )

        assert response.status_code == 200
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("No hay presupuestos" in m for m in msgs)

    def test_copy_success_all_copied(
        self, authenticated_client, user, expense_category_factory, budget_factory
    ):
        url = reverse("budgets:copy")
        today = timezone.now().date()

        target_month = today.month
        target_year = today.year

        if target_month == 1:
            source_month = 12
            source_year = target_year - 1
        else:
            source_month = target_month - 1
            source_year = target_year

        cat1 = expense_category_factory(user, name="Origen 1")
        cat2 = expense_category_factory(user, name="Origen 2")

        budget_factory(user, cat1, month=source_month, year=source_year, amount=Decimal("100.00"))
        budget_factory(user, cat2, month=source_month, year=source_year, amount=Decimal("200.00"))

        response = authenticated_client.post(
            url,
            {"target_month": target_month, "target_year": target_year},
            follow=False,
        )

        assert response.status_code == 302
        assert f"month={target_month}" in response["Location"]
        assert f"year={target_year}" in response["Location"]

        assert Budget.objects.filter(
            user=user, category=cat1, month=target_month, year=target_year
        ).exists()
        assert Budget.objects.filter(
            user=user, category=cat2, month=target_month, year=target_year
        ).exists()

    def test_copy_partial_skips_existing(
        self, authenticated_client, user, expense_category_factory, budget_factory
    ):
        url = reverse("budgets:copy")
        today = timezone.now().date()

        target_month = today.month
        target_year = today.year

        if target_month == 1:
            source_month = 12
            source_year = target_year - 1
        else:
            source_month = target_month - 1
            source_year = target_year

        cat1 = expense_category_factory(user, name="Origen 1")
        cat2 = expense_category_factory(user, name="Origen 2")

        budget_factory(user, cat1, month=source_month, year=source_year, amount=Decimal("100.00"))
        budget_factory(user, cat2, month=source_month, year=source_year, amount=Decimal("200.00"))

        # cat2 ya existe en destino => se omite
        budget_factory(user, cat2, month=target_month, year=target_year, amount=Decimal("999.00"))

        response = authenticated_client.post(
            url,
            {"target_month": target_month, "target_year": target_year},
            follow=True,
        )

        assert response.status_code == 200
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("ya existían y se omitieron" in m for m in msgs)

        assert Budget.objects.filter(
            user=user, category=cat1, month=target_month, year=target_year
        ).exists()

    def test_copy_all_skipped_when_all_exist(
        self, authenticated_client, user, expense_category_factory, budget_factory
    ):
        url = reverse("budgets:copy")
        today = timezone.now().date()

        target_month = today.month
        target_year = today.year

        if target_month == 1:
            source_month = 12
            source_year = target_year - 1
        else:
            source_month = target_month - 1
            source_year = target_year

        cat1 = expense_category_factory(user, name="Origen 1")
        cat2 = expense_category_factory(user, name="Origen 2")

        # origen
        budget_factory(user, cat1, month=source_month, year=source_year, amount=Decimal("100.00"))
        budget_factory(user, cat2, month=source_month, year=source_year, amount=Decimal("200.00"))

        # destino ya tiene ambos => 0 copiados
        budget_factory(user, cat1, month=target_month, year=target_year, amount=Decimal("111.00"))
        budget_factory(user, cat2, month=target_month, year=target_year, amount=Decimal("222.00"))

        response = authenticated_client.post(
            url,
            {"target_month": target_month, "target_year": target_year},
            follow=True,
        )

        assert response.status_code == 200
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("ya existen" in m for m in msgs)
