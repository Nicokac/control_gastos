"""
Configuración global de pytest y fixtures compartidas.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType, Currency
from apps.users.models import User

# =============================================================================
# USER FIXTURES
# =============================================================================


@pytest.fixture
def user(db):
    """Crea un usuario de prueba."""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def other_user(db):
    """Crea otro usuario de prueba (para tests de permisos)."""
    return User.objects.create_user(
        username="otheruser", email="other@example.com", password="otherpass123"
    )


@pytest.fixture
def admin_user(db):
    """Crea un usuario administrador."""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )


# =============================================================================
# CLIENT FIXTURES
# =============================================================================


@pytest.fixture
def authenticated_client(client, user):
    """Cliente autenticado con el usuario de prueba."""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Cliente autenticado con el usuario admin."""
    client.login(username="admin", password="adminpass123")
    return client


@pytest.fixture
def other_user_client(client, other_user):
    """Cliente autenticado con otro usuario."""
    client.force_login(other_user)
    return client


# =============================================================================
# DATE FIXTURES
# =============================================================================


@pytest.fixture
def today():
    """Retorna la fecha de hoy."""
    return timezone.now().date()


@pytest.fixture
def yesterday(today):
    """Retorna la fecha de ayer."""
    return today - timedelta(days=1)


@pytest.fixture
def tomorrow(today):
    """Retorna la fecha de mañana."""
    return today + timedelta(days=1)


@pytest.fixture
def next_month(today):
    """Retorna una fecha del próximo mes."""
    if today.month == 12:
        return date(today.year + 1, 1, 15)
    return date(today.year, today.month + 1, 15)


@pytest.fixture
def last_month(today):
    """Retorna una fecha del mes pasado."""
    if today.month == 1:
        return date(today.year - 1, 12, 15)
    return date(today.year, today.month - 1, 15)


@pytest.fixture
def current_month():
    """Retorna el mes actual."""
    return timezone.now().month


@pytest.fixture
def current_year():
    """Retorna el año actual."""
    return timezone.now().year


# =============================================================================
# AMOUNT FIXTURES
# =============================================================================


@pytest.fixture
def sample_amount():
    """Monto de ejemplo en ARS."""
    return Decimal("1500.50")


@pytest.fixture
def sample_usd_amount():
    """Monto en USD de ejemplo."""
    return Decimal("100.00")


@pytest.fixture
def exchange_rate():
    """Tipo de cambio de ejemplo."""
    return Decimal("1150.00")


# =============================================================================
# CATEGORY FACTORIES
# =============================================================================


@pytest.fixture
def expense_category_factory(db):
    """Factory para crear categorías de gasto."""

    def _create_category(user=None, **kwargs):
        defaults = {
            "name": "Categoría Gasto Test",
            "type": CategoryType.EXPENSE,
            "icon": "bi-cart",
            "color": "#FF5733",
            "user": user,
            "is_system": user is None,
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)

    return _create_category


@pytest.fixture
def income_category_factory(db):
    """Factory para crear categorías de ingreso."""

    def _create_category(user=None, **kwargs):
        defaults = {
            "name": "Categoría Ingreso Test",
            "type": CategoryType.INCOME,
            "icon": "bi-cash",
            "color": "#28A745",
            "user": user,
            "is_system": user is None,
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)

    return _create_category


# =============================================================================
# CATEGORY FIXTURES (usando factories)
# =============================================================================


@pytest.fixture
def expense_category(user, expense_category_factory):
    """Crea una categoría de gasto para el usuario de prueba."""
    return expense_category_factory(user=user, name="Alimentación")


@pytest.fixture
def income_category(user, income_category_factory):
    """Crea una categoría de ingreso para el usuario de prueba."""
    return income_category_factory(user=user, name="Salario")


@pytest.fixture
def system_expense_category(expense_category_factory):
    """Crea una categoría de sistema (gasto)."""
    return expense_category_factory(user=None, name="Otros Gastos", is_system=True)


@pytest.fixture
def system_income_category(income_category_factory):
    """Crea una categoría de sistema (ingreso)."""
    return income_category_factory(user=None, name="Otros Ingresos", is_system=True)


# =============================================================================
# EXPENSE FACTORY
# =============================================================================


@pytest.fixture
def expense_factory(db):
    """Factory para crear gastos."""

    def _create_expense(user, category, **kwargs):
        from apps.expenses.models import Expense

        defaults = {
            "user": user,
            "category": category,
            "date": timezone.now().date(),
            "description": "Gasto de prueba",
            "amount": Decimal("100.00"),
            "currency": Currency.ARS,
            "exchange_rate": Decimal("1.00"),
        }
        defaults.update(kwargs)
        return Expense.objects.create(**defaults)

    return _create_expense


@pytest.fixture
def expense(user, expense_category, expense_factory):
    """Crea un gasto de prueba."""
    return expense_factory(user, expense_category)


# =============================================================================
# INCOME FACTORY
# =============================================================================


@pytest.fixture
def income_factory(db):
    """Factory para crear ingresos."""

    def _create_income(user, category, **kwargs):
        from apps.income.models import Income

        defaults = {
            "user": user,
            "category": category,
            "date": timezone.now().date(),
            "description": "Ingreso de prueba",
            "amount": Decimal("1000.00"),
            "currency": Currency.ARS,
            "exchange_rate": Decimal("1.00"),
        }
        defaults.update(kwargs)
        return Income.objects.create(**defaults)

    return _create_income


@pytest.fixture
def income(user, income_category, income_factory):
    """Crea un ingreso de prueba."""
    return income_factory(user, income_category)


# =============================================================================
# BUDGET FACTORY
# =============================================================================


@pytest.fixture
def budget_factory(db):
    """Factory para crear presupuestos."""

    def _create_budget(user, category, **kwargs):
        from apps.budgets.models import Budget

        today = timezone.now().date()
        defaults = {
            "user": user,
            "category": category,
            "month": today.month,
            "year": today.year,
            "amount": Decimal("5000.00"),
            "alert_threshold": 80,
        }
        defaults.update(kwargs)
        return Budget.objects.create(**defaults)

    return _create_budget


@pytest.fixture
def budget(user, expense_category, budget_factory):
    """Crea un presupuesto de prueba."""
    return budget_factory(user, expense_category)


# =============================================================================
# SAVING FACTORY
# =============================================================================


@pytest.fixture
def saving_factory(db):
    """Factory para crear metas de ahorro."""

    def _create_saving(user, **kwargs):
        from apps.savings.models import Saving

        defaults = {
            "user": user,
            "name": "Meta de prueba",
            "target_amount": Decimal("10000.00"),
            "current_amount": Decimal("0.00"),
        }
        defaults.update(kwargs)
        return Saving.objects.create(**defaults)

    return _create_saving


@pytest.fixture
def saving(user, saving_factory):
    """Crea una meta de ahorro de prueba."""
    return saving_factory(user)


@pytest.fixture
def saving_with_progress(user, saving_factory):
    """Crea una meta de ahorro con progreso."""
    return saving_factory(user, current_amount=Decimal("5000.00"))


# =============================================================================
# SAVING MOVEMENT FACTORY
# =============================================================================


@pytest.fixture
def saving_movement_factory(db):
    """Factory para crear movimientos de ahorro."""

    def _create_movement(saving, movement_type="DEPOSIT", **kwargs):
        from apps.savings.models import SavingMovement

        defaults = {
            "saving": saving,
            "type": movement_type,
            "amount": Decimal("1000.00"),
            "date": timezone.now().date(),
            # 'notes': 'Movimiento de prueba',  # ELIMINAR - Campo no existe
        }
        defaults.update(kwargs)
        return SavingMovement.objects.create(**defaults)

    return _create_movement


# ============================================================
# Helpers para URLs
# ============================================================


def get_url(name, **kwargs):
    """
    Helper para obtener URL con fallback de namespace.
    Intenta primero sin namespace, luego con namespace común.
    """
    from django.urls import NoReverseMatch, reverse

    # Mapeo de posibles namespaces
    namespace_map = {
        "dashboard": ["dashboard", "reports:dashboard", "core:dashboard"],
        "home": ["home", "core:home"],
    }

    # Si el nombre está en el mapeo, probar variantes
    if name in namespace_map:
        for variant in namespace_map[name]:
            try:
                return reverse(variant, kwargs=kwargs)
            except NoReverseMatch:
                continue
        raise NoReverseMatch(f"No se encontró URL para '{name}'")

    # Si no, intentar directamente
    return reverse(name, kwargs=kwargs)


@pytest.fixture
def url_helper():
    """Fixture que expone el helper de URLs."""
    return get_url
