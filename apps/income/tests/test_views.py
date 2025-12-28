"""
Tests para las vistas de Income.
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone

from apps.income.models import Income
from apps.core.constants import Currency


@pytest.mark.django_db
class TestIncomeListView:
    """Tests para la vista de listado de ingresos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse('income:list')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_list_user_income(self, authenticated_client, income):
        """Verifica que liste los ingresos del usuario."""
        url = reverse('income:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert income.description in response.content.decode()

    def test_excludes_other_user_income(self, authenticated_client, other_user, income_category_factory, income_factory):
        """Verifica que no muestre ingresos de otros usuarios."""
        other_cat = income_category_factory(other_user, name='Otra')
        other_income = income_factory(other_user, other_cat, description='Ingreso Otro')
        
        url = reverse('income:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'Ingreso Otro' not in response.content.decode()


@pytest.mark.django_db
class TestIncomeCreateView:
    """Tests para la vista de creación de ingresos."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse('income:create')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_get_create_form(self, authenticated_client):
        """Verifica que muestre el formulario de creación."""
        url = reverse('income:create')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context

    def test_create_income_ars_success(self, authenticated_client, user, income_category):
        """Verifica creación exitosa de ingreso en ARS."""
        url = reverse('income:create')
        data = {
            'category': income_category.pk,
            'description': 'Nuevo Ingreso',
            'amount': '50000.00',
            'currency': Currency.ARS,
            'date': timezone.now().date().isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 302
        assert Income.objects.filter(description='Nuevo Ingreso', user=user).exists()

    def test_create_income_usd_success(self, authenticated_client, user, income_category):
        """Verifica creación exitosa de ingreso en USD."""
        url = reverse('income:create')
        data = {
            'category': income_category.pk,
            'description': 'Ingreso USD',
            'amount': '500.00',
            'currency': Currency.USD,
            'exchange_rate': '1200.00',
            'date': timezone.now().date().isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 302
        
        income = Income.objects.get(description='Ingreso USD')
        assert income.currency == Currency.USD

    def test_income_assigned_to_current_user(self, authenticated_client, user, income_category):
        """Verifica que el ingreso se asigne al usuario actual."""
        url = reverse('income:create')
        data = {
            'category': income_category.pk,
            'description': 'Mi Ingreso',
            'amount': '100000.00',
            'currency': Currency.ARS,
            'date': timezone.now().date().isoformat(),
        }
        
        authenticated_client.post(url, data)
        
        income = Income.objects.get(description='Mi Ingreso')
        assert income.user == user


@pytest.mark.django_db
class TestIncomeUpdateView:
    """Tests para la vista de edición de ingresos."""

    def test_login_required(self, client, income):
        """Verifica que requiera autenticación."""
        url = reverse('income:update', kwargs={'pk': income.pk})
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_get_update_form(self, authenticated_client, income):
        """Verifica que muestre el formulario de edición."""
        url = reverse('income:update', kwargs={'pk': income.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'form' in response.context

    def test_update_income_success(self, authenticated_client, income):
        """Verifica edición exitosa de ingreso."""
        url = reverse('income:update', kwargs={'pk': income.pk})
        data = {
            'category': income.category.pk,
            'description': 'Descripción Actualizada',
            'amount': str(income.amount),
            'currency': income.currency,
            'date': income.date.isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 302
        
        income.refresh_from_db()
        assert income.description == 'Descripción Actualizada'

    def test_cannot_update_other_user_income(self, authenticated_client, other_user, income_category_factory, income_factory):
        """Verifica que no pueda editar ingresos de otros usuarios."""
        other_cat = income_category_factory(other_user, name='Otra')
        other_income = income_factory(other_user, other_cat)
        
        url = reverse('income:update', kwargs={'pk': other_income.pk})
        response = authenticated_client.get(url)
        
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestIncomeDeleteView:
    """Tests para la vista de eliminación de ingresos."""

    def test_login_required(self, client, income):
        """Verifica que requiera autenticación."""
        url = reverse('income:delete', kwargs={'pk': income.pk})
        response = client.post(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_delete_income_success(self, authenticated_client, income):
        """Verifica eliminación exitosa de ingreso."""
        url = reverse('income:delete', kwargs={'pk': income.pk})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == 302
        
        income.refresh_from_db()
        assert income.is_active == False

    def test_cannot_delete_other_user_income(self, authenticated_client, other_user, income_category_factory, income_factory):
        """Verifica que no pueda eliminar ingresos de otros usuarios."""
        other_cat = income_category_factory(other_user, name='Otra')
        other_income = income_factory(other_user, other_cat)
        
        url = reverse('income:delete', kwargs={'pk': other_income.pk})
        response = authenticated_client.post(url)
        
        assert response.status_code in [403, 404]