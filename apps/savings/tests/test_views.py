"""
Tests para las vistas de Saving.
"""

from decimal import Decimal

from django.urls import reverse

import pytest

from apps.savings.forms import SavingForm
from apps.savings.models import Saving, SavingStatus


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
        # Crear una meta de otro usuario que no debería aparecer en el listado
        saving_factory(other_user, name="Otra Meta")

        url = reverse("savings:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "Otra Meta" not in response.content.decode()


@pytest.mark.django_db
class TestSavingListViewFilters:
    def test_list_filters_by_valid_status(self, authenticated_client, user, saving_factory):
        s_active = saving_factory(user, name="Meta Activa X", status=SavingStatus.ACTIVE)
        s_completed = saving_factory(user, name="Meta Completada Y", status=SavingStatus.COMPLETED)

        url = reverse("savings:list")
        response = authenticated_client.get(url, {"status": SavingStatus.COMPLETED})

        assert response.status_code == 200
        content = response.content.decode()
        assert s_completed.name in content
        assert s_active.name not in content

    def test_list_ignores_invalid_status_filter(self, authenticated_client, user, saving_factory):
        saving_factory(user, name="Activa", status=SavingStatus.ACTIVE)
        saving_factory(user, name="Completada", status=SavingStatus.COMPLETED)

        url = reverse("savings:list")
        response = authenticated_client.get(url, {"status": "NOT_A_REAL_STATUS"})

        assert response.status_code == 200
        content = response.content.decode()
        # Si ignora el filtro, deberían aparecer ambas
        assert "Activa" in content
        assert "Completada" in content


@pytest.mark.django_db
class TestSavingListViewSummary:
    def test_summary_overall_progress_zero_when_no_active_savings(self, authenticated_client):
        url = reverse("savings:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        summary = response.context["summary"]
        assert summary["overall_progress"] == 0
        assert summary["total_target"] == Decimal("0")
        assert summary["total_current"] == Decimal("0")
        assert summary["total_remaining"] == Decimal("0")


@pytest.mark.django_db
class TestSavingListViewSummaryCap:
    def test_summary_overall_progress_capped_to_100(
        self, authenticated_client, user, saving_factory
    ):
        # ACTIVE y is_active=True => entra en active_savings
        saving_factory(
            user,
            name="Meta",
            status=SavingStatus.ACTIVE,
            target_amount=Decimal("100.00"),
            current_amount=Decimal("250.00"),  # > target
        )

        url = reverse("savings:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        summary = response.context["summary"]
        assert summary["overall_progress"] == 100


@pytest.mark.django_db
class TestSavingDetailViewPagination:
    def test_detail_page_not_an_integer_defaults_to_page_1(
        self, authenticated_client, saving, saving_movement_factory
    ):
        # Crear 12 movimientos para tener 2 páginas
        for _ in range(12):
            saving_movement_factory(saving, "DEPOSIT", amount=Decimal("1.00"))

        url = reverse("savings:detail", kwargs={"pk": saving.pk})
        response = authenticated_client.get(url, {"page": "nope"})

        assert response.status_code == 200
        movements = response.context["movements"]
        assert movements.number == 1  # PageNotAnInteger => page(1)

    def test_detail_empty_page_returns_last_page(
        self, authenticated_client, saving, saving_movement_factory
    ):
        for _ in range(12):
            saving_movement_factory(saving, "DEPOSIT", amount=Decimal("1.00"))

        url = reverse("savings:detail", kwargs={"pk": saving.pk})
        response = authenticated_client.get(url, {"page": "9999"})

        assert response.status_code == 200
        movements = response.context["movements"]
        assert movements.number == movements.paginator.num_pages  # EmptyPage => last page


@pytest.mark.django_db
class TestSavingMovementCreateView:
    def test_create_movement_deposit_shows_success_message(self, authenticated_client, saving):
        url = reverse("savings:add_movement", kwargs={"pk": saving.pk})
        data = {"type": "DEPOSIT", "amount": "100.00", "description": "Dep"}

        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        msgs = [m.message for m in response.context["messages"]]
        assert any("Depósito" in m for m in msgs)

    def test_create_movement_withdrawal_shows_success_message(
        self, authenticated_client, saving_with_progress
    ):
        url = reverse("savings:add_movement", kwargs={"pk": saving_with_progress.pk})
        data = {"type": "WITHDRAWAL", "amount": "10.00", "description": "W"}

        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        msgs = [m.message for m in response.context["messages"]]
        assert any("Retiro" in m for m in msgs)

    def test_create_movement_invalid_shows_error_message(self, authenticated_client, saving):
        url = reverse("savings:add_movement", kwargs={"pk": saving.pk})
        data = {"type": "DEPOSIT", "amount": "", "description": "bad"}  # inválido

        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        msgs = [m.message for m in response.context["messages"]]
        assert any("Corregí los errores" in m for m in msgs)

    def test_cannot_add_movement_to_other_users_saving(
        self, authenticated_client, other_user, saving_factory
    ):
        other_saving = saving_factory(other_user, name="Ajena")
        url = reverse("savings:add_movement", kwargs={"pk": other_saving.pk})

        response = authenticated_client.get(url)
        assert response.status_code == 404

    def test_movement_create_redirects_to_detail(self, authenticated_client, saving):
        url = reverse("savings:add_movement", kwargs={"pk": saving.pk})
        data = {"type": "DEPOSIT", "amount": "1.00", "description": ""}

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert reverse("savings:detail", kwargs={"pk": saving.pk}) in response.url


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

        assert not Saving.objects.filter(pk=saving.pk).exists()


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
