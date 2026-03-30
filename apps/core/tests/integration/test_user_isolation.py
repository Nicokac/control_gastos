"""
Tests de integraciÃ³n para verificar aislamiento de datos entre usuarios.
"""

from decimal import Decimal

from django.urls import reverse

import pytest

from apps.expenses.models import Expense


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestUserDataIsolation:
    """Tests de aislamiento de datos entre usuarios."""

    def test_user_cannot_see_other_user_expenses(
        self, authenticated_client, user, other_user, expense_category_factory, expense_factory
    ):
        """Verifica que un usuario no vea gastos de otro."""
        other_cat = expense_category_factory(other_user, name="Otra Cat")
        expense_factory(
            other_user, other_cat, description="Gasto Secreto", amount=Decimal("9999.00")
        )

        list_url = reverse("expenses:list")
        response = authenticated_client.get(list_url)

        content = response.content.decode()
        assert "Gasto Secreto" not in content
        assert "9999" not in content

    def test_user_cannot_see_other_user_income(
        self, authenticated_client, user, other_user, income_category_factory, income_factory
    ):
        """Verifica que un usuario no vea ingresos de otro."""
        other_cat = income_category_factory(other_user, name="Otra Cat Income")
        income_factory(
            other_user, other_cat, description="Ingreso Secreto", amount=Decimal("999999.00")
        )

        list_url = reverse("income:list")
        response = authenticated_client.get(list_url)

        content = response.content.decode()
        assert "Ingreso Secreto" not in content

    def test_user_cannot_see_other_user_savings(
        self, authenticated_client, user, other_user, saving_factory
    ):
        """Verifica que un usuario no vea metas de ahorro de otro."""
        saving_factory(other_user, name="Meta Secreta", target_amount=Decimal("1000000.00"))

        list_url = reverse("savings:list")
        response = authenticated_client.get(list_url)

        content = response.content.decode()
        assert "Meta Secreta" not in content

    def test_user_cannot_edit_other_user_expense(
        self, authenticated_client, user, other_user, expense_category_factory, expense_factory
    ):
        """Verifica que un usuario no pueda editar gastos de otro."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_expense = expense_factory(other_user, other_cat)

        edit_url = reverse("expenses:update", kwargs={"pk": other_expense.pk})
        response = authenticated_client.get(edit_url)

        assert response.status_code in [403, 404]

    def test_user_cannot_delete_other_user_expense(
        self, authenticated_client, user, other_user, expense_category_factory, expense_factory
    ):
        """Verifica que un usuario no pueda eliminar gastos de otro."""
        other_cat = expense_category_factory(other_user, name="Otra")
        other_expense = expense_factory(other_user, other_cat)

        delete_url = reverse("expenses:delete", kwargs={"pk": other_expense.pk})
        response = authenticated_client.post(delete_url)

        assert response.status_code in [403, 404]

        other_expense.refresh_from_db()
        assert Expense.objects.filter(pk=other_expense.pk).exists()

    def test_user_cannot_access_other_user_saving_movements(
        self, authenticated_client, user, other_user, saving_factory
    ):
        """Verifica que un usuario no pueda agregar movimientos a metas de otro."""
        other_saving = saving_factory(other_user, name="Meta Ajena")

        movement_url = reverse("savings:add_movement", kwargs={"pk": other_saving.pk})
        response = authenticated_client.get(movement_url)

        assert response.status_code in [403, 404]
