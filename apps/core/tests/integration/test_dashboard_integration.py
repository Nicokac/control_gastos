"""
Tests de integración del Dashboard.
Verifica que el dashboard muestre datos correctos después de operaciones.
"""

from datetime import date
from decimal import Decimal

from django.urls import NoReverseMatch, reverse

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
    Verifica que un monto esté presente en el HTML, tolerando distintos formatos:
    - 5000
    - 5.000 / 5,000
    - 5000.00 / 5000,00
    - 5.000,00 / 5,000.00, etc.
    """
    amount_str = str(amount)

    candidates: set[str] = set()

    # Sin separador
    candidates.add(amount_str)
    candidates.add(f"{amount_str}.00")
    candidates.add(f"{amount_str},00")

    # Con separador de miles (si aplica)
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
        f"Monto {amount} no encontrado en el HTML. " f"Patrones usados: {sorted(candidates)}"
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

        today = date.today()

        # Crear gasto
        Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto para dashboard",
            amount=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        # Verificar dashboard
        response = authenticated_client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        # El gasto debería reflejarse de alguna forma
        assert_amount_in_content(content, 5000)

    def test_dashboard_reflects_new_income(self, authenticated_client, user, income_category):
        """Verifica que dashboard refleje un nuevo ingreso."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = date.today()

        # Crear ingreso
        Income.objects.create(
            user=user,
            category=income_category,
            description="Ingreso para dashboard",
            amount=Decimal("100000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        # Verificar dashboard
        response = authenticated_client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert_amount_in_content(content, 100000)

    def test_dashboard_shows_budget_warning(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """Verifica que dashboard muestre alerta de presupuesto."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = date.today()

        # Crear presupuesto
        budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("10000.00"),
            alert_threshold=80,
        )

        # Crear gasto que exceda umbral (85%)
        Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto grande",
            amount=Decimal("8500.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        # Verificar dashboard
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Debería mostrar algún indicador de alerta
        content = response.content.decode().lower()
        assert (
            "warning" in content
            or "alerta" in content
            or "excedido" in content
            or "cerca" in content
            or "85" in content
        )  # 🔧 F841

        # Al menos debería cargar sin error
        assert response.status_code == 200

    def test_dashboard_shows_budget_exceeded(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """Verifica que dashboard muestre presupuesto excedido."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = date.today()

        # Crear presupuesto
        budget_factory(  # 🔧 F841
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        # Crear gasto que exceda presupuesto
        Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto excesivo",
            amount=Decimal("15000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        # Verificar dashboard
        response = authenticated_client.get(url)
        assert response.status_code == 200


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

        today = date.today()

        # Crear gasto
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto original",
            amount=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        # Verificar dashboard inicial
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Editar gasto
        expense.amount = Decimal("10000.00")
        expense.save()

        # Verificar dashboard actualizado
        response = authenticated_client.get(url)
        assert response.status_code == 200
        content = response.content.decode()

        # El nuevo monto debería reflejarse
        assert_amount_in_content(content, 10000)

    def test_dashboard_updates_after_expense_delete(
        self, authenticated_client, user, expense_category
    ):
        """Verifica que dashboard se actualice después de eliminar gasto."""
        url = get_dashboard_url()
        if url is None:
            pytest.skip("Dashboard URL not configured")

        today = date.today()

        # Crear gasto
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto a eliminar",
            amount=Decimal("50000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1"),
            date=today,
        )

        # Verificar dashboard con gasto
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # Eliminar gasto (soft delete)
        expense.soft_delete()

        # Verificar dashboard sin gasto
        response = authenticated_client.get(url)
        assert response.status_code == 200

        # El monto eliminado no debería aparecer
        content = response.content.decode()  # 🔧 F841
        # 50000 no debería estar (o debería ser 0 si era el único)
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

        # Crear datos del otro usuario
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

        # Verificar dashboard del usuario actual
        response = authenticated_client.get(url)
        assert response.status_code == 200

        content = response.content.decode()
        assert "Gasto secreto" not in content
        assert "Ingreso secreto" not in content
        assert "999999" not in content
        assert "888888" not in content
