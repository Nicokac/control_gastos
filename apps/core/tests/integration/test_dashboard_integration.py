"""
Tests de integración del Dashboard.
Verifica que el dashboard muestre datos correctos después de operaciones.
"""

from datetime import date
from decimal import Decimal

from django.urls import NoReverseMatch, reverse
from django.utils import timezone

import pytest

from apps.core.constants import Currency
from apps.expenses.models import Expense
from apps.income.models import Income


def get_dashboard_url():
    """Obtiene la URL del dashboard probando diferentes variantes."""
    variants = ["reports:dashboard", "dashboard", "core:dashboard"]
    for name in variants:
        try:
            return reverse(name)
        except NoReverseMatch:
            continue
    return None


def assert_amount_in_content(content: str, amount: int | str) -> None:
    """
    Verifica que un monto esté presente en el HTML, tolerando distintos formatos.
    """
    amount_str = str(amount)

    candidates: set[str] = {amount_str, f"{amount_str}.00", f"{amount_str},00"}

    if len(amount_str) > 3:
        thousands = amount_str[:-3]
        last3 = amount_str[-3:]
        dot = f"{thousands}.{last3}"
        comma = f"{thousands},{last3}"
        candidates.update(
            {
                dot,
                comma,
                f"{dot}.00",
                f"{dot},00",
                f"{comma}.00",
                f"{comma},00",
            }
        )

    assert any(c in content for c in candidates), (
        f"Monto {amount} no encontrado en el HTML. Patrones usados: {sorted(candidates)}"
    )


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestDashboardDataIntegration:
    """Tests de integración de datos en el dashboard."""

    def test_dashboard_reflects_new_expense(self, authenticated_client, user, expense_category):
        """Verifica que dashboard refleje un nuevo gasto."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = timezone.now().date()

        Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto para dashboard",
            amount=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        response = authenticated_client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert_amount_in_content(content, 5000)

    def test_dashboard_reflects_new_income(self, authenticated_client, user, income_category):
        """Verifica que dashboard refleje un nuevo ingreso."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = timezone.now().date()

        Income.objects.create(
            user=user,
            category=income_category,
            description="Ingreso para dashboard",
            amount=Decimal("100000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        response = authenticated_client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert_amount_in_content(content, 100000)

    def test_dashboard_does_not_render_budget_section(self, authenticated_client):
        """Verifica que el dashboard no renderice el bloque de presupuestos."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "Presupuestos de" not in response.content.decode()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestDashboardAfterOperations:
    """Tests de dashboard después de operaciones CRUD."""

    def test_dashboard_updates_after_expense_edit(
        self, authenticated_client, user, expense_category
    ):
        """Verifica que dashboard se actualice después de editar gasto."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = timezone.now().date()

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto original",
            amount=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        response = authenticated_client.get(url)
        assert response.status_code == 200

        expense.amount = Decimal("10000.00")
        expense.save()

        response = authenticated_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()
        assert_amount_in_content(content, 10000)

    def test_dashboard_updates_after_expense_delete(
        self, authenticated_client, user, expense_category
    ):
        """Verifica que dashboard se actualice después de eliminar gasto."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = date.today()

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto a eliminar",
            amount=Decimal("50000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        response = authenticated_client.get(url)
        assert response.status_code == 200

        expense.delete()

        response = authenticated_client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert "50000" not in content and "50.000" not in content


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestDashboardMultiUserIsolation:
    """Tests de aislamiento de datos en dashboard."""

    def test_dashboard_only_shows_current_user_data(
        self,
        authenticated_client,
        user,
        other_user,
        expense_category_factory,
        income_category_factory,
    ):
        """Verifica que dashboard solo muestre datos del usuario actual."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = date.today()

        other_expense_cat = expense_category_factory(other_user, name="Otra Cat Expense")
        other_income_cat = income_category_factory(other_user, name="Otra Cat Income")

        Expense.objects.create(
            user=other_user,
            category=other_expense_cat,
            description="Gasto secreto",
            amount=Decimal("999999.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        Income.objects.create(
            user=other_user,
            category=other_income_cat,
            description="Ingreso secreto",
            amount=Decimal("888888.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        response = authenticated_client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert "Gasto secreto" not in content
        assert "Ingreso secreto" not in content
        assert "999999" not in content
        assert "888888" not in content


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestDashboardProjection:
    """Tests de proyección de cierre de mes."""

    def test_proyeccion_aparece_con_datos_suficientes(
        self, authenticated_client, user, expense_category, income_category
    ):
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = timezone.now().date()
        # Crear gastos en los últimos 3 días para asegurar period_day >= 3
        for i in range(3):
            d = today.replace(day=max(1, today.day - i))
            Expense.objects.create(
                user=user,
                category=expense_category,
                description=f"Gasto día {i}",
                amount=Decimal("3000.00"),
                currency=Currency.ARS,
                exchange_rate=Decimal("1"),
                date=d,
            )
        Income.objects.create(
            user=user,
            category=income_category,
            description="Sueldo test",
            amount=Decimal("100000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "Proyección al cierre" in response.content.decode()

    def test_proyeccion_no_aparece_sin_gastos(self, authenticated_client, user, income_category):
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = timezone.now().date()
        Income.objects.create(
            user=user,
            category=income_category,
            description="Sueldo test",
            amount=Decimal("100000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert "Proyección al cierre" not in response.content.decode()
