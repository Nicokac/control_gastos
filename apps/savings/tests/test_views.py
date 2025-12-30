"""
Tests para las vistas de Saving.
"""

from decimal import Decimal

from django.urls import reverse

import pytest

from apps.savings.forms import SavingForm
from apps.savings.models import Saving


@pytest.mark.django_db
class TestSavingListView:
    """Tests para la vista de listado de metas de ahorro."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("savings:list")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_list_user_savings(self, authenticated_client, saving):
        """Verifica que liste las metas del usuario."""
        url = reverse("savings:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert saving.name in response.content.decode()

    def test_excludes_other_user_savings(self, authenticated_client, other_user, saving_factory):
        """Verifica que no muestre metas de otros usuarios."""
        other_saving = saving_factory(other_user, name="Otra Meta")

        url = reverse("savings:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "Otra Meta" not in response.content.decode()


@pytest.mark.django_db
class TestSavingCreateView:
    """Tests para la vista de creación de metas de ahorro."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("savings:create")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_create_form(self, authenticated_client):
        """Verifica que muestre el formulario de creación."""
        url = reverse("savings:create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_create_saving_success(self, authenticated_client, user):
        """Verifica creación exitosa de meta de ahorro."""
        # Obtener valores válidos del form
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields["icon"].choices)
        color_choices = list(temp_form.fields["color"].choices)

        url = reverse("savings:create")
        data = {
            "name": "Nueva Meta",
            "target_amount": "100000.00",
            "currency": "ARS",
            "icon": icon_choices[0][0] if icon_choices else "bi-piggy-bank",
            "color": color_choices[0][0] if color_choices else "green",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert Saving.objects.filter(name="Nueva Meta", user=user).exists()

    def test_saving_assigned_to_current_user(self, authenticated_client, user):
        """Verifica que la meta se asigne al usuario actual."""
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields["icon"].choices)
        color_choices = list(temp_form.fields["color"].choices)

        url = reverse("savings:create")
        data = {
            "name": "Mi Meta",
            "target_amount": "50000.00",
            "currency": "ARS",
            "icon": icon_choices[0][0] if icon_choices else "bi-piggy-bank",
            "color": color_choices[0][0] if color_choices else "green",
        }

        authenticated_client.post(url, data)

        saving = Saving.objects.get(name="Mi Meta")
        assert saving.user == user


@pytest.mark.django_db
class TestSavingUpdateView:
    """Tests para la vista de edición de metas de ahorro."""

    def test_login_required(self, client, saving):
        """Verifica que requiera autenticación."""
        url = reverse("savings:update", kwargs={"pk": saving.pk})
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_update_form(self, authenticated_client, saving):
        """Verifica que muestre el formulario de edición."""
        url = reverse("savings:update", kwargs={"pk": saving.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_cannot_update_other_user_saving(
        self, authenticated_client, other_user, saving_factory
    ):
        """Verifica que no pueda editar metas de otros usuarios."""
        other_saving = saving_factory(other_user, name="Otra")

        url = reverse("savings:update", kwargs={"pk": other_saving.pk})
        response = authenticated_client.get(url)

        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestSavingDeleteView:
    """Tests para la vista de eliminación de metas de ahorro."""

    def test_login_required(self, client, saving):
        """Verifica que requiera autenticación."""
        url = reverse("savings:delete", kwargs={"pk": saving.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_delete_saving_success(self, authenticated_client, saving):
        """Verifica eliminación exitosa de meta."""
        url = reverse("savings:delete", kwargs={"pk": saving.pk})

        response = authenticated_client.post(url)

        assert response.status_code == 302

        saving.refresh_from_db()
        assert saving.is_active == False


@pytest.mark.django_db
class TestSavingMovementView:
    """Tests para la vista de movimientos de ahorro."""

    def test_login_required(self, client, user, saving_factory):
        """Verifica que requiera autenticación."""
        # Crear saving con un usuario específico
        saving = saving_factory(user)

        url = reverse("savings:add_movement", kwargs={"pk": saving.pk})

        # Usar cliente sin autenticar
        response = client.get(url)

        # Debería redirigir a login
        assert response.status_code == 302
        assert "login" in response.url

    def test_add_deposit_success(self, authenticated_client, saving):
        """Verifica agregar depósito exitosamente."""
        url = reverse("savings:add_movement", kwargs={"pk": saving.pk})
        data = {
            "type": "DEPOSIT",
            "amount": "5000.00",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("5000.00")

    def test_add_withdrawal_success(self, authenticated_client, saving_with_progress):
        """Verifica agregar retiro exitosamente."""
        initial_amount = saving_with_progress.current_amount

        url = reverse("savings:add_movement", kwargs={"pk": saving_with_progress.pk})
        data = {
            "type": "WITHDRAWAL",
            "amount": "1000.00",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302

        saving_with_progress.refresh_from_db()
        assert saving_with_progress.current_amount == initial_amount - Decimal("1000.00")

    def test_withdrawal_cannot_exceed_balance(self, authenticated_client, saving):
        """Verifica que retiro no exceda el saldo."""
        url = reverse("savings:add_movement", kwargs={"pk": saving.pk})
        data = {
            "type": "WITHDRAWAL",
            "amount": "10000.00",  # Más que el saldo (0)
        }

        response = authenticated_client.post(url, data)

        # Debería mostrar error
        assert response.status_code == 200
        assert "form" in response.context
