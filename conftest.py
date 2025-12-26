"""
Configuración global de pytest y fixtures compartidas.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import date, timedelta

from apps.users.models import User
from apps.categories.models import Category
from apps.core.constants import CategoryType, Currency


@pytest.fixture
def user(db):
    """Crea un usuario de prueba."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def other_user(db):
    """Crea otro usuario de prueba (para tests de permisos)."""
    return User.objects.create_user(
        username='otheruser',
        email='other@example.com',
        password='otherpass123'
    )


@pytest.fixture
def admin_user(db):
    """Crea un usuario administrador."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def expense_category(db, user):
    """Crea una categoría de gasto."""
    return Category.objects.create(
        name='Alimentación',
        type=CategoryType.EXPENSE,
        icon='bi-cart',
        color='#FF5733',
        user=user,
        is_system=False
    )


@pytest.fixture
def income_category(db, user):
    """Crea una categoría de ingreso."""
    return Category.objects.create(
        name='Salario',
        type=CategoryType.INCOME,
        icon='bi-cash',
        color='#28A745',
        user=user,
        is_system=False
    )


@pytest.fixture
def system_expense_category(db):
    """Crea una categoría de sistema (gasto)."""
    return Category.objects.create(
        name='Otros Gastos',
        type=CategoryType.EXPENSE,
        icon='bi-three-dots',
        color='#6C757D',
        user=None,
        is_system=True
    )


@pytest.fixture
def system_income_category(db):
    """Crea una categoría de sistema (ingreso)."""
    return Category.objects.create(
        name='Otros Ingresos',
        type=CategoryType.INCOME,
        icon='bi-three-dots',
        color='#6C757D',
        user=None,
        is_system=True
    )


@pytest.fixture
def today():
    """Retorna la fecha de hoy."""
    return timezone.now().date()


@pytest.fixture
def yesterday(today):
    """Retorna la fecha de ayer."""
    return today - timedelta(days=1)


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
def authenticated_client(client, user):
    """Cliente autenticado con el usuario de prueba."""
    client.login(username='testuser', password='testpass123')
    return client


@pytest.fixture
def sample_amount():
    """Monto de ejemplo."""
    return Decimal('1500.50')


@pytest.fixture
def sample_usd_amount():
    """Monto en USD de ejemplo."""
    return Decimal('100.00')


@pytest.fixture
def exchange_rate():
    """Tipo de cambio de ejemplo."""
    return Decimal('1150.00')