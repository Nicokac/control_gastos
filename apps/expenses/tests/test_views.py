"""
Tests para las vistas de Expense.
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone

from apps.expenses.models import Expense
from apps.core.constants import Currency


@pytest.mark.django_db
class TestExpenseListView:
    """Tests para la vista de listado de gastos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse('expenses:list')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_list_user_expenses(self, authenticated_client, expense):
        """Verifica que liste los gastos del usuario."""
        url = reverse('expenses:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert expense.description in response.content.decode()

    def test_excludes_other_user_expenses(self, authenticated_client, other_user, expense_category_factory, expense_factory):
        """Verifica que no muestre gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name='Otra')
        other_expense = expense_factory(other_user, other_cat, description='Gasto Otro')
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'Gasto Otro' not in response.content.decode()

    def test_filter_by_month(self, authenticated_client, user, expense_category, expense_factory):
        """Verifica filtrado por mes."""
        today = timezone.now().date()
        expense_factory(user, expense_category, description='Este Mes', date=today)
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url, {'month': today.month, 'year': today.year})
        
        assert response.status_code == 200
        assert 'Este Mes' in response.content.decode()

    def test_filter_by_category(self, authenticated_client, user, expense_category, expense_factory):
        """Verifica filtrado por categoría."""
        expense_factory(user, expense_category, description='Filtrado')
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url, {'category': expense_category.pk})
        
        assert response.status_code == 200
        assert 'Filtrado' in response.content.decode()


@pytest.mark.django_db
class TestExpenseCreateView:
    """Tests para la vista de creación de gastos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse('expenses:create')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_get_create_form(self, authenticated_client):
        """Verifica que muestre el formulario de creación."""
        url = reverse('expenses:create')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context

    def test_create_expense_ars_success(self, authenticated_client, user, expense_category):
        """Verifica creación exitosa de gasto en ARS."""
        url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Nuevo Gasto',
            'amount': '1500.00',
            'currency': Currency.ARS,
            'date': timezone.now().date().isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 302
        assert Expense.objects.filter(description='Nuevo Gasto', user=user).exists()

    def test_create_expense_usd_success(self, authenticated_client, user, expense_category):
        """Verifica creación exitosa de gasto en USD."""
        url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Gasto USD',
            'amount': '100.00',
            'currency': Currency.USD,
            'exchange_rate': '1150.00',
            'date': timezone.now().date().isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 302
        
        expense = Expense.objects.get(description='Gasto USD')
        assert expense.currency == Currency.USD
        assert expense.exchange_rate == Decimal('1150.00')

    def test_create_expense_invalid_data(self, authenticated_client, expense_category):
        """Verifica que no cree con datos inválidos."""
        url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': '',  # Descripción vacía
            'amount': '100.00',
            'currency': Currency.ARS,
            'date': timezone.now().date().isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_expense_assigned_to_current_user(self, authenticated_client, user, expense_category):
        """Verifica que el gasto se asigne al usuario actual."""
        url = reverse('expenses:create')
        data = {
            'category': expense_category.pk,
            'description': 'Mi Gasto',
            'amount': '500.00',
            'currency': Currency.ARS,
            'date': timezone.now().date().isoformat(),
        }
        
        authenticated_client.post(url, data)
        
        expense = Expense.objects.get(description='Mi Gasto')
        assert expense.user == user

    def test_only_user_categories_in_form(self, authenticated_client, user, expense_category, other_user, expense_category_factory):
        """Verifica que solo muestre categorías del usuario en el form."""
        other_cat = expense_category_factory(other_user, name='Otra')
        
        url = reverse('expenses:create')
        response = authenticated_client.get(url)
        
        form = response.context['form']
        category_pks = [c.pk for c in form.fields['category'].queryset]
        
        assert expense_category.pk in category_pks
        assert other_cat.pk not in category_pks


@pytest.mark.django_db
class TestExpenseUpdateView:
    """Tests para la vista de edición de gastos."""

    def test_login_required(self, client, expense):
        """Verifica que requiera autenticación."""
        url = reverse('expenses:update', kwargs={'pk': expense.pk})
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_get_update_form(self, authenticated_client, expense):
        """Verifica que muestre el formulario de edición."""
        url = reverse('expenses:update', kwargs={'pk': expense.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].instance == expense

    def test_update_expense_success(self, authenticated_client, expense):
        """Verifica edición exitosa de gasto."""
        url = reverse('expenses:update', kwargs={'pk': expense.pk})
        data = {
            'category': expense.category.pk,
            'description': 'Descripción Actualizada',
            'amount': str(expense.amount),
            'currency': expense.currency,
            'date': expense.date.isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 302
        
        expense.refresh_from_db()
        assert expense.description == 'Descripción Actualizada'

    def test_cannot_update_other_user_expense(self, authenticated_client, other_user, expense_category_factory, expense_factory):
        """Verifica que no pueda editar gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name='Otra')
        other_expense = expense_factory(other_user, other_cat)
        
        url = reverse('expenses:update', kwargs={'pk': other_expense.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestExpenseDeleteView:
    """Tests para la vista de eliminación de gastos."""

    def test_login_required(self, client, expense):
        """Verifica que requiera autenticación."""
        url = reverse('expenses:delete', kwargs={'pk': expense.pk})
        response = client.post(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_delete_expense_success(self, authenticated_client, expense):
        """Verifica eliminación exitosa de gasto."""
        url = reverse('expenses:delete', kwargs={'pk': expense.pk})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == 302
        
        expense.refresh_from_db()
        assert expense.is_active == False

    def test_cannot_delete_other_user_expense(self, authenticated_client, other_user, expense_category_factory, expense_factory):
        """Verifica que no pueda eliminar gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name='Otra')
        other_expense = expense_factory(other_user, other_cat)
        
        url = reverse('expenses:delete', kwargs={'pk': other_expense.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestExpenseDetailView:
    """Tests para la vista de detalle de gasto."""

    def test_login_required(self, client, expense):
        """Verifica que requiera autenticación."""
        url = reverse('expenses:detail', kwargs={'pk': expense.pk})
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_view_expense_detail(self, authenticated_client, expense):
        """Verifica que muestre el detalle del gasto."""
        url = reverse('expenses:detail', kwargs={'pk': expense.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert expense.description in response.content.decode()

    def test_cannot_view_other_user_expense(self, authenticated_client, other_user, expense_category_factory, expense_factory):
        """Verifica que no pueda ver gastos de otros usuarios."""
        other_cat = expense_category_factory(other_user, name='Otra')
        other_expense = expense_factory(other_user, other_cat)
        
        url = reverse('expenses:detail', kwargs={'pk': other_expense.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code in [403, 404]