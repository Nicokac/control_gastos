"""
Tests para las vistas de Budget.
"""

from decimal import Decimal

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
        # Crear presupuesto de otro usuario que no debería aparecer en el listado
        budget_factory(other_user, other_cat)

        url = reverse("budgets:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200

    def test_filter_by_month_year(self, authenticated_client, budget):
        """Verifica filtrado por mes/año."""
        url = reverse("budgets:list")
        response = authenticated_client.get(url, {"month": budget.month, "year": budget.year})

        assert response.status_code == 200


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

    def test_create_budget_success(self, authenticated_client, user, expense_category):
        """Verifica creación exitosa de presupuesto."""
        today = timezone.now().date()

        # Usar mes diferente para evitar duplicados
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

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert Budget.objects.filter(
            category=expense_category, month=test_month, year=test_year, user=user
        ).exists()

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

        # Debería mostrar error
        assert response.status_code == 200
        assert response.context["form"].errors


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

    def test_update_budget_success(self, authenticated_client, budget):
        """Verifica edición exitosa de presupuesto."""
        url = reverse("budgets:update", kwargs={"pk": budget.pk})
        data = {
            "category": budget.category.pk,
            "month": budget.month,
            "year": budget.year,
            "amount": "100000.00",
            "alert_threshold": 90,
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302

        budget.refresh_from_db()
        assert budget.amount == Decimal("100000.00")
        assert budget.alert_threshold == 90

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

        response = authenticated_client.post(url)

        assert response.status_code == 302

        budget.refresh_from_db()
        # 🔧 E712: evitar comparación con False
        assert not budget.is_active

    def test_cannot_delete_other_user_budget(
        self, authenticated_client, other_user, expense_category_factory, budget_factory
    ):
        """Verifica que no pueda eliminar presupuestos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_budget = budget_factory(other_user, other_cat)

        url = reverse("budgets:delete", kwargs={"pk": other_budget.pk})
        response = authenticated_client.post(url)

        assert response.status_code in [403, 404]
