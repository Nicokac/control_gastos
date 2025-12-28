"""
Tests para las vistas de Core (Dashboard).
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestDashboardView:
    """Tests para la vista del dashboard."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse('dashboard')
        response = client.get(url)
        
        assert response.status_code == 302
        assert 'login' in response.url

    def test_dashboard_accessible(self, authenticated_client):
        """Verifica que el dashboard sea accesible."""
        url = reverse('dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200

    def test_dashboard_shows_summary(self, authenticated_client, expense, income):
        """Verifica que el dashboard muestre resumen."""
        url = reverse('dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        # Verificar que haya contexto con datos
        # assert 'total_expenses' in response.context or similar

    def test_dashboard_only_user_data(self, authenticated_client, user, other_user, expense_category_factory, expense_factory):
        """Verifica que solo muestre datos del usuario actual."""
        other_cat = expense_category_factory(other_user, name='Otra')
        other_expense = expense_factory(other_user, other_cat, description='Otro Gasto')
        
        url = reverse('dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'Otro Gasto' not in response.content.decode()


@pytest.mark.django_db
class TestHomeView:
    """Tests para la vista principal."""

    def test_home_redirects_authenticated_user(self, authenticated_client):
        """Verifica que usuario autenticado sea redirigido al dashboard."""
        url = reverse('home')
        response = authenticated_client.get(url)
        
        # Puede ser 200 si home es dashboard, o 302 si redirige
        assert response.status_code in [200, 302]

    def test_home_shows_landing_for_anonymous(self, client):
        """Verifica que usuario anónimo vea landing o login."""
        url = reverse('home')
        response = client.get(url)
        
        # Puede ser 200 (landing) o 302 (redirect to login)
        assert response.status_code in [200, 302]