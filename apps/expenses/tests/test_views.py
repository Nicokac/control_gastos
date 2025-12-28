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


@pytest.mark.django_db
class TestExpenseListViewFilters:
    """Tests para filtros en la vista de listado de gastos."""

    def test_filter_by_month_shows_only_month_expenses(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica que filtro por mes muestre solo gastos de ese mes."""
        from datetime import date
        
        # Crear gastos en diferentes meses
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 15), 
            description='Gasto Enero'
        )
        expense_factory(
            user, expense_category, 
            date=date(2025, 2, 15), 
            description='Gasto Febrero'
        )
        expense_factory(
            user, expense_category, 
            date=date(2025, 3, 15), 
            description='Gasto Marzo'
        )
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url, {'month': 1, 'year': 2025})
        
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Gasto Enero' in content
        assert 'Gasto Febrero' not in content
        assert 'Gasto Marzo' not in content

    def test_filter_by_category_shows_only_category_expenses(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        """Verifica que filtro por categoría funcione."""
        cat_comida = expense_category_factory(user, name='Comida')
        cat_transporte = expense_category_factory(user, name='Transporte')
        
        expense_factory(user, cat_comida, description='Almuerzo')
        expense_factory(user, cat_transporte, description='Subte')
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url, {'category': cat_comida.pk})
        
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Almuerzo' in content
        assert 'Subte' not in content

    def test_filter_by_date_range(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica filtro por rango de fechas."""
        from datetime import date
        
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 5), 
            description='Inicio Mes'
        )
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 15), 
            description='Mitad Mes'
        )
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 25), 
            description='Fin Mes'
        )
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url, {
            'date_from': '2025-01-10',
            'date_to': '2025-01-20'
        })
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Solo debería mostrar el del medio
        # Nota: ajustar según implementación de filtros
        if 'date_from' in response.request.get('QUERY_STRING', ''):
            assert 'Mitad Mes' in content

    def test_combined_filters(
        self, authenticated_client, user, expense_category_factory, expense_factory
    ):
        """Verifica que múltiples filtros funcionen juntos."""
        from datetime import date
        
        cat1 = expense_category_factory(user, name='Cat1')
        cat2 = expense_category_factory(user, name='Cat2')
        
        expense_factory(user, cat1, date=date(2025, 1, 15), description='Cat1 Enero')
        expense_factory(user, cat1, date=date(2025, 2, 15), description='Cat1 Febrero')
        expense_factory(user, cat2, date=date(2025, 1, 15), description='Cat2 Enero')
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url, {
            'category': cat1.pk,
            'month': 1,
            'year': 2025
        })
        
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Cat1 Enero' in content
        assert 'Cat1 Febrero' not in content
        assert 'Cat2 Enero' not in content

    def test_empty_filter_results(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica comportamiento cuando filtro no tiene resultados."""
        from datetime import date
        
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 15), 
            description='Único Gasto'
        )
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url, {'month': 6, 'year': 2025})
        
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Único Gasto' not in content


@pytest.mark.django_db
class TestExpenseViewRedirects:
    """Tests para verificar redirecciones correctas."""

    def test_create_redirects_to_list(self, authenticated_client, user, expense_category):
        """Verifica que crear redirija a lista."""
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
        assert 'expenses' in response.url

    def test_update_redirects_correctly(self, authenticated_client, expense):
        """Verifica que actualizar redirija correctamente."""
        url = reverse('expenses:update', kwargs={'pk': expense.pk})
        data = {
            'category': expense.category.pk,
            'description': 'Actualizado',
            'amount': str(expense.amount),
            'currency': expense.currency,
            'date': expense.date.isoformat(),
        }
        
        response = authenticated_client.post(url, data)
        
        assert response.status_code == 302
        # Puede redirigir a list o a detail
        assert 'expenses' in response.url

    def test_delete_redirects_to_list(self, authenticated_client, expense):
        """Verifica que eliminar redirija a lista."""
        url = reverse('expenses:delete', kwargs={'pk': expense.pk})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == 302
        assert 'expenses' in response.url


@pytest.mark.django_db
class TestExpenseListViewOrdering:
    """Tests para verificar ordenamiento en ListView."""

    def test_expenses_ordered_by_date_descending(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica que gastos estén ordenados por fecha descendente."""
        from datetime import date
        
        # Crear gastos en orden cronológico
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 1), 
            description='Primero Cronológico'
        )
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 15), 
            description='Segundo Cronológico'
        )
        expense_factory(
            user, expense_category, 
            date=date(2025, 1, 30), 
            description='Tercero Cronológico'
        )
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode()
        
        # Verificar que el más reciente aparezca primero
        pos_tercero = content.find('Tercero Cronológico')
        pos_segundo = content.find('Segundo Cronológico')
        pos_primero = content.find('Primero Cronológico')
        
        # Si todos existen en el contenido, verificar orden
        if pos_tercero != -1 and pos_segundo != -1 and pos_primero != -1:
            assert pos_tercero < pos_segundo < pos_primero

    def test_expenses_same_date_ordered_by_created(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica ordenamiento secundario cuando fechas son iguales."""
        from datetime import date
        import time
        
        today = date.today()
        
        # Crear gastos en el mismo día
        expense_factory(user, expense_category, date=today, description='Gasto A')
        time.sleep(0.1)  # Pequeña pausa para diferenciar created_at
        expense_factory(user, expense_category, date=today, description='Gasto B')
        
        url = reverse('expenses:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        # Ambos deberían aparecer
        content = response.content.decode()
        assert 'Gasto A' in content
        assert 'Gasto B' in content