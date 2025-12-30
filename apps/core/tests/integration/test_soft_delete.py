"""
Tests de integración para soft delete.
"""

from datetime import date
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.expenses.models import Expense
from apps.savings.models import Saving


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestSoftDeleteBehavior:
    """Tests de comportamiento de soft delete."""

    def test_deleted_expense_not_in_list(self, authenticated_client, expense):
        """Verifica que gasto eliminado no aparezca en lista."""
        # Eliminar
        delete_url = reverse("expenses:delete", kwargs={"pk": expense.pk})
        authenticated_client.post(delete_url)

        # Verificar que no aparece en lista
        list_url = reverse("expenses:list")
        response = authenticated_client.get(list_url)

        assert expense.description not in response.content.decode()

    def test_deleted_expense_still_in_database(self, authenticated_client, expense):
        """Verifica que gasto eliminado siga en DB."""
        pk = expense.pk

        delete_url = reverse("expenses:delete", kwargs={"pk": pk})
        authenticated_client.post(delete_url)

        # Debería existir con all_objects
        deleted = Expense.all_objects.get(pk=pk)
        assert deleted.is_active == False
        assert deleted.deleted_at is not None

    def test_deleted_expense_not_counted_in_budget(
        self, authenticated_client, user, expense_category, budget_factory, expense_factory
    ):
        """Verifica que gasto eliminado no cuente en presupuesto."""
        today = date.today()

        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        # Crear gasto
        expense = expense_factory(user, expense_category, amount=Decimal("3000.00"), date=today)

        budget.refresh_from_db()
        assert budget.spent_amount == Decimal("3000.00")

        # Eliminar gasto
        delete_url = reverse("expenses:delete", kwargs={"pk": expense.pk})
        authenticated_client.post(delete_url)

        # Presupuesto debería actualizarse
        budget.refresh_from_db()
        assert budget.spent_amount == Decimal("0")

    def test_deleted_category_not_in_form_choices(
        self, authenticated_client, user, expense_category
    ):
        """Verifica que categoría eliminada no aparezca en formularios."""
        # Eliminar categoría
        delete_url = reverse("categories:delete", kwargs={"pk": expense_category.pk})
        authenticated_client.post(delete_url)

        # Ir a crear gasto
        create_url = reverse("expenses:create")
        response = authenticated_client.get(create_url)

        # La categoría eliminada no debería estar en el form
        form = response.context["form"]
        category_pks = [c.pk for c in form.fields["category"].queryset]

        assert expense_category.pk not in category_pks

    def test_deleted_saving_movements_preserved(self, authenticated_client, user, saving):
        """Verifica que movimientos de meta eliminada se preserven."""
        # Agregar movimiento
        movement_url = reverse("savings:add_movement", kwargs={"pk": saving.pk})
        authenticated_client.post(
            movement_url,
            {
                "type": "DEPOSIT",
                "amount": "5000.00",
            },
        )

        # Eliminar meta
        delete_url = reverse("savings:delete", kwargs={"pk": saving.pk})
        authenticated_client.post(delete_url)

        # Verificar que meta y movimientos siguen en DB
        from apps.savings.models import SavingMovement

        saving_deleted = Saving.all_objects.get(pk=saving.pk)
        assert saving_deleted.is_active == False

        movements = SavingMovement.objects.filter(saving=saving)
        assert movements.count() >= 1


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestSoftDeleteRecovery:
    """Tests de recuperación de datos eliminados (si aplica)."""

    def test_soft_deleted_data_recoverable_via_all_objects(self, authenticated_client, expense):
        """Verifica que datos eliminados sean recuperables."""
        pk = expense.pk
        description = expense.description

        # Eliminar
        delete_url = reverse("expenses:delete", kwargs={"pk": pk})
        authenticated_client.post(delete_url)

        # No visible con objects
        assert not Expense.objects.filter(pk=pk).exists()

        # Visible con all_objects
        deleted = Expense.all_objects.get(pk=pk)
        assert deleted.description == description
        assert deleted.is_active == False

    def test_multiple_soft_deletes_tracked(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Verifica tracking de múltiples eliminaciones."""
        # Crear varios gastos
        expenses = [
            expense_factory(user, expense_category, description=f"Gasto {i}") for i in range(3)
        ]

        # Eliminar todos
        for expense in expenses:
            delete_url = reverse("expenses:delete", kwargs={"pk": expense.pk})
            authenticated_client.post(delete_url)

        # Verificar todos eliminados pero en DB
        active_count = Expense.objects.filter(user=user).count()
        all_count = Expense.all_objects.filter(user=user).count()

        assert active_count == 0
        assert all_count >= 3
