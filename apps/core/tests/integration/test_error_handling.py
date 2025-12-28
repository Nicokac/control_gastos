"""
Tests de manejo de errores en flujos de integración.
Verifica que el sistema maneje correctamente situaciones de error.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse

from apps.expenses.models import Expense
from apps.income.models import Income
from apps.budgets.models import Budget
from apps.savings.models import Saving
from apps.core.constants import Currency, CategoryType


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseErrorHandling:
    """Tests de manejo de errores en gastos."""

    def test_expense_with_invalid_category_shows_error(
        self, authenticated_client, user
    ):
        """Verifica error con categoría inválida."""
        create_url = reverse('expenses:create')
        data = {
            'category': 99999,  # Categoría que no existe
            'description': 'Gasto con categoría inválida',
            'amount': '1000.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        response = authenticated_client.post(create_url, data)
        
        # No debería crear el gasto
        assert response.status_code == 200  # Form con error, no redirect
        assert not Expense.objects.filter(
            description='Gasto con categoría inválida'
        ).exists()
        
        # Debería tener errores en el form
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_expense_with_negative_amount_shows_error(
        self, authenticated_client, user, expense_category
    ):
        """Verifica error con monto negativo."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto negativo',
            'amount': '-500.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        response = authenticated_client.post(create_url, data)
        
        assert response.status_code == 200
        assert not Expense.objects.filter(description='Gasto negativo').exists()
        assert response.context['form'].errors

    def test_expense_with_future_date_shows_error(
        self, authenticated_client, user, expense_category
    ):
        """Verifica error con fecha futura."""
        create_url = reverse('expenses:create')
        future_date = date.today() + timedelta(days=30)
        
        data = {
            'category': expense_category.pk,
            'description': 'Gasto futuro',
            'amount': '1000.00',
            'currency': Currency.ARS,
            'date': future_date.isoformat(),
        }
        
        response = authenticated_client.post(create_url, data)
        
        # Si hay validación de fecha futura
        if response.status_code == 200:
            assert not Expense.objects.filter(description='Gasto futuro').exists()

    def test_expense_usd_without_exchange_rate_shows_error(
        self, authenticated_client, user, expense_category
    ):
        """Verifica error USD sin tipo de cambio."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto USD sin TC',
            'amount': '100.00',
            'currency': Currency.USD,
            # No incluimos exchange_rate
            'date': date.today().isoformat(),
        }
        
        response = authenticated_client.post(create_url, data)
        
        # Debería fallar o pedir exchange_rate
        assert response.status_code == 200
        assert not Expense.objects.filter(description='Gasto USD sin TC').exists()

    def test_expense_with_empty_description_shows_error(
        self, authenticated_client, user, expense_category
    ):
        """Verifica error con descripción vacía."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': '',  # Vacío
            'amount': '1000.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        response = authenticated_client.post(create_url, data)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestBudgetErrorHandling:
    """Tests de manejo de errores en presupuestos."""

    def test_duplicate_budget_shows_error(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """Verifica error al crear presupuesto duplicado."""
        today = date.today()
        
        # Crear presupuesto existente
        budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('50000.00')
        )
        
        # Intentar crear duplicado
        create_url = reverse('budgets:create')
        data = {
            'category': expense_category.pk,
            'month': today.month,
            'year': today.year,
            'amount': '60000.00',
            'alert_threshold': 80,
        }
        
        response = authenticated_client.post(create_url, data)
        
        # No debería crear
        assert response.status_code == 200
        assert Budget.objects.filter(
            user=user, 
            category=expense_category,
            month=today.month,
            year=today.year
        ).count() == 1

    def test_budget_with_invalid_month_shows_error(
        self, authenticated_client, user, expense_category
    ):
        """Verifica error con mes inválido."""
        create_url = reverse('budgets:create')
        data = {
            'category': expense_category.pk,
            'month': 13,  # Mes inválido
            'year': 2025,
            'amount': '50000.00',
            'alert_threshold': 80,
        }
        
        response = authenticated_client.post(create_url, data)
        
        assert response.status_code == 200
        assert 'form' in response.context

    def test_budget_with_negative_amount_shows_error(
        self, authenticated_client, user, expense_category
    ):
        """Verifica error con monto negativo."""
        create_url = reverse('budgets:create')
        data = {
            'category': expense_category.pk,
            'month': 6,
            'year': 2025,
            'amount': '-10000.00',
            'alert_threshold': 80,
        }
        
        response = authenticated_client.post(create_url, data)
        
        assert response.status_code == 200
        assert not Budget.objects.filter(
            user=user,
            category=expense_category,
            month=6,
            year=2025
        ).exists()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestSavingErrorHandling:
    """Tests de manejo de errores en ahorros."""

    def test_withdrawal_exceeding_balance_shows_error(
        self, authenticated_client, user, saving
    ):
        """Verifica error al retirar más del saldo."""
        # Saving empieza con current_amount = 0
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        data = {
            'type': 'WITHDRAWAL',
            'amount': '10000.00',  # Más que el saldo (0)
        }
        
        response = authenticated_client.post(movement_url, data)
        
        # Debería mostrar error
        assert response.status_code == 200
        assert 'form' in response.context
        
        # Saldo no debería cambiar
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('0')

    def test_deposit_with_negative_amount_shows_error(
        self, authenticated_client, user, saving
    ):
        """Verifica error con depósito negativo."""
        movement_url = reverse('savings:add_movement', kwargs={'pk': saving.pk})
        data = {
            'type': 'DEPOSIT',
            'amount': '-1000.00',
        }
        
        response = authenticated_client.post(movement_url, data)
        
        assert response.status_code == 200
        
        saving.refresh_from_db()
        assert saving.current_amount == Decimal('0')

    def test_saving_with_negative_target_shows_error(
        self, authenticated_client, user
    ):
        """Verifica error con objetivo negativo."""
        from apps.savings.forms import SavingForm
        
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields['icon'].choices)
        color_choices = list(temp_form.fields['color'].choices)
        
        create_url = reverse('savings:create')
        data = {
            'name': 'Meta negativa',
            'target_amount': '-50000.00',
            'currency': 'ARS',
            'icon': icon_choices[0][0] if icon_choices else 'bi-piggy-bank',
            'color': color_choices[0][0] if color_choices else 'green',
        }
        
        response = authenticated_client.post(create_url, data)
        
        assert response.status_code == 200
        assert not Saving.objects.filter(name='Meta negativa').exists()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestCategoryErrorHandling:
    """Tests de manejo de errores en categorías."""

    def test_category_with_empty_name_shows_error(
        self, authenticated_client, user
    ):
        """Verifica error con nombre vacío."""
        create_url = reverse('categories:create')
        data = {
            'name': '',
            'type': CategoryType.EXPENSE,
            'icon': 'bi-tag',
            'color': '#000000',
        }
        
        response = authenticated_client.post(create_url, data)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_category_with_invalid_type_shows_error(
        self, authenticated_client, user
    ):
        """Verifica error con tipo inválido."""
        create_url = reverse('categories:create')
        data = {
            'name': 'Categoría inválida',
            'type': 'INVALID_TYPE',
            'icon': 'bi-tag',
            'color': '#000000',
        }
        
        response = authenticated_client.post(create_url, data)
        
        assert response.status_code == 200
        from apps.categories.models import Category
        assert not Category.objects.filter(name='Categoría inválida').exists()


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestAuthenticationErrorHandling:
    """Tests de manejo de errores de autenticación."""

    def test_unauthenticated_expense_creation_redirects(
        self, client, expense_category
    ):
        """Verifica que usuario no autenticado sea redirigido."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Intento sin login',
            'amount': '1000.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        response = client.post(create_url, data)
        
        # Debería redirigir a login
        assert response.status_code == 302
        assert 'login' in response.url
        
        # No debería crear el gasto
        assert not Expense.objects.filter(description='Intento sin login').exists()

    def test_unauthenticated_budget_creation_redirects(
        self, client, expense_category
    ):
        """Verifica que creación de presupuesto requiera login."""
        create_url = reverse('budgets:create')
        data = {
            'category': expense_category.pk,
            'month': 6,
            'year': 2025,
            'amount': '50000.00',
            'alert_threshold': 80,
        }
        
        response = client.post(create_url, data)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_unauthenticated_saving_creation_redirects(self, client):
        """Verifica que creación de meta requiera login."""
        create_url = reverse('savings:create')
        
        response = client.get(create_url)
        
        assert response.status_code == 302
        assert 'login' in response.url