"""
Tests de integración para el flujo completo de gastos.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse

from apps.expenses.models import Expense
from apps.categories.models import Category
from apps.budgets.models import Budget
from apps.core.constants import Currency, CategoryType


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseCreationFlow:
    """Tests del flujo completo de creación de gastos."""

    def test_create_expense_and_verify_in_list(
        self, authenticated_client, user, expense_category
    ):
        """Verifica que un gasto creado aparezca en la lista."""
        # 1. Crear gasto
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Compra supermercado',
            'amount': '2500.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        response = authenticated_client.post(create_url, data)
        assert response.status_code == 302  # Redirect después de crear
        
        # 2. Verificar que existe en DB
        expense = Expense.objects.get(description='Compra supermercado')
        assert expense.user == user
        assert expense.amount == Decimal('2500.00')
        
        # 3. Verificar que aparece en lista
        list_url = reverse('expenses:list')
        response = authenticated_client.get(list_url)
        
        assert response.status_code == 200
        assert 'Compra supermercado' in response.content.decode()

    def test_create_edit_delete_expense_flow(
        self, authenticated_client, user, expense_category
    ):
        """Verifica flujo completo: crear -> editar -> eliminar."""
        # 1. CREAR
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto Original',
            'amount': '1000.00',
            'currency': Currency.ARS,
            'date': date.today().isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        expense = Expense.objects.get(description='Gasto Original')
        
        # 2. EDITAR
        edit_url = reverse('expenses:update', kwargs={'pk': expense.pk})
        data['description'] = 'Gasto Editado'
        data['amount'] = '1500.00'
        
        response = authenticated_client.post(edit_url, data)
        assert response.status_code == 302
        
        expense.refresh_from_db()
        assert expense.description == 'Gasto Editado'
        assert expense.amount == Decimal('1500.00')
        
        # 3. ELIMINAR (soft delete)
        delete_url = reverse('expenses:delete', kwargs={'pk': expense.pk})
        response = authenticated_client.post(delete_url)
        assert response.status_code == 302
        
        expense.refresh_from_db()
        assert expense.is_active == False
        
        # 4. Verificar que no aparece en lista
        list_url = reverse('expenses:list')
        response = authenticated_client.get(list_url)
        assert 'Gasto Editado' not in response.content.decode()

    def test_expense_with_usd_currency_flow(
        self, authenticated_client, user, expense_category
    ):
        """Verifica flujo de gasto en USD con tipo de cambio."""
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Compra Amazon',
            'amount': '50.00',
            'currency': Currency.USD,
            'exchange_rate': '1200.00',
            'date': date.today().isoformat(),
        }
        
        response = authenticated_client.post(create_url, data)
        assert response.status_code == 302
        
        expense = Expense.objects.get(description='Compra Amazon')
        assert expense.currency == Currency.USD
        assert expense.amount == Decimal('50.00')
        assert expense.exchange_rate == Decimal('1200.00')
        assert expense.amount_ars == Decimal('60000.00')  # 50 * 1200


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseBudgetIntegration:
    """Tests de integración entre gastos y presupuestos."""

    def test_expense_affects_budget_spent(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """Verifica que un gasto afecte el presupuesto."""
        today = date.today()
        
        # 1. Crear presupuesto
        budget = budget_factory(
            user, 
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        assert budget.spent_amount == Decimal('0')
        
        # 2. Crear gasto
        create_url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto con presupuesto',
            'amount': '3000.00',
            'currency': Currency.ARS,
            'date': today.isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        # 3. Verificar que presupuesto se actualizó
        budget.refresh_from_db()
        assert budget.spent_amount == Decimal('3000.00')
        assert budget.remaining_amount == Decimal('7000.00')
        assert budget.spent_percentage == Decimal('30.0')

    def test_multiple_expenses_accumulate_in_budget(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """Verifica que múltiples gastos se acumulen en el presupuesto."""
        today = date.today()
        
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        create_url = reverse('expenses:create')
        
        # Crear 3 gastos
        for i in range(3):
            data = {
                'category': expense_category.pk,
                'description': f'Gasto {i+1}',
                'amount': '2000.00',
                'currency': Currency.ARS,
                'date': today.isoformat(),
            }
            authenticated_client.post(create_url, data)
        
        budget.refresh_from_db()
        assert budget.spent_amount == Decimal('6000.00')
        assert budget.spent_percentage == Decimal('60.0')

    def test_budget_over_limit_detection(
        self, authenticated_client, user, expense_category, budget_factory
    ):
        """Verifica detección de presupuesto excedido."""
        today = date.today()
        
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('5000.00'),
            alert_threshold=80
        )
        
        create_url = reverse('expenses:create')
        
        # Gasto que excede el presupuesto
        data = {
            'category': expense_category.pk,
            'description': 'Gasto grande',
            'amount': '6000.00',
            'currency': Currency.ARS,
            'date': today.isoformat(),
        }
        
        authenticated_client.post(create_url, data)
        
        budget.refresh_from_db()
        assert budget.is_over_budget == True
        assert budget.spent_percentage > 100


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseFilteringFlow:
    """Tests de filtrado de gastos."""

    def test_filter_expenses_by_month(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica filtrado de gastos por mes."""
        # Crear gastos en diferentes meses
        expense_factory(
            user, expense_category,
            description='Gasto Enero',
            date=date(2025, 1, 15)
        )
        expense_factory(
            user, expense_category,
            description='Gasto Febrero',
            date=date(2025, 2, 15)
        )
        
        # Filtrar por enero
        list_url = reverse('expenses:list')
        response = authenticated_client.get(list_url, {'month': 1, 'year': 2025})
        
        content = response.content.decode()
        assert 'Gasto Enero' in content
        assert 'Gasto Febrero' not in content

    def test_filter_expenses_by_category(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        """Verifica filtrado de gastos por categoría."""
        cat_comida = expense_category_factory(user, name='Comida')
        cat_transporte = expense_category_factory(user, name='Transporte')
        
        expense_factory(user, cat_comida, description='Almuerzo')
        expense_factory(user, cat_transporte, description='Uber')
        
        # Filtrar por comida
        list_url = reverse('expenses:list')
        response = authenticated_client.get(list_url, {'category': cat_comida.pk})
        
        content = response.content.decode()
        assert 'Almuerzo' in content
        assert 'Uber' not in content