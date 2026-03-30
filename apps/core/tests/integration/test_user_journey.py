"""
Tests de journey completo de usuario.
Simula el flujo real que seguirÃ­a un usuario nuevo en la aplicaciÃ³n.
"""

from datetime import date
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType, Currency
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.savings.forms import SavingForm
from apps.savings.models import Saving, SavingStatus


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestNewUserJourney:
    """Tests del flujo completo de un usuario nuevo."""

    def test_complete_expense_tracking_journey(self, authenticated_client, user):
        """
        Simula journey completo de tracking de gastos:
        1. Crear categorÃ­a
        2. Registrar gastos
        3. Editar gasto
        4. Eliminar gasto
        """
        today = date.today()

        cat_url = reverse("categories:create")
        cat_data = {
            "name": "Supermercado",
            "type": CategoryType.EXPENSE,
            "icon": "bi-cart",
            "color": "#28a745",
        }

        response = authenticated_client.post(cat_url, cat_data)
        assert response.status_code == 302

        category = Category.objects.get(name="Supermercado", user=user)
        assert category.type == CategoryType.EXPENSE

        expense_url = reverse("expenses:create")

        expense_data_1 = {
            "category": category.pk,
            "description": "Compra semanal",
            "amount": "15000.00",
            "currency": Currency.ARS,
            "date": today.isoformat(),
        }

        response = authenticated_client.post(expense_url, expense_data_1)
        assert response.status_code == 302

        expense_1 = Expense.objects.get(description="Compra semanal")
        assert expense_1.amount == Decimal("15000.00")

        expense_data_2 = {
            "category": category.pk,
            "description": "VerdulerÃ­a",
            "amount": "5000.00",
            "currency": Currency.ARS,
            "date": today.isoformat(),
        }

        response = authenticated_client.post(expense_url, expense_data_2)
        assert response.status_code == 302

        edit_url = reverse("expenses:update", kwargs={"pk": expense_1.pk})
        expense_data_1["description"] = "Compra semanal (editada)"
        expense_data_1["amount"] = "18000.00"

        response = authenticated_client.post(edit_url, expense_data_1)
        assert response.status_code == 302

        expense_1.refresh_from_db()
        assert expense_1.description == "Compra semanal (editada)"
        assert expense_1.amount == Decimal("18000.00")

        expense_2 = Expense.objects.get(description="VerdulerÃ­a")
        delete_url = reverse("expenses:delete", kwargs={"pk": expense_2.pk})

        response = authenticated_client.post(delete_url)
        assert response.status_code == 302
        assert not Expense.objects.filter(pk=expense_2.pk).exists()

    def test_complete_income_tracking_journey(self, authenticated_client, user):
        """
        Simula journey completo de tracking de ingresos:
        1. Crear categorÃ­a de ingreso
        2. Registrar ingresos (ARS y USD)
        3. Verificar totales
        """
        today = date.today()

        cat_url = reverse("categories:create")
        cat_data = {
            "name": "Trabajo",
            "type": CategoryType.INCOME,
            "icon": "bi-briefcase",
            "color": "#007bff",
        }

        response = authenticated_client.post(cat_url, cat_data)
        assert response.status_code == 302

        category = Category.objects.get(name="Trabajo", user=user)

        income_url = reverse("income:create")

        income_data_ars = {
            "category": category.pk,
            "description": "Sueldo mensual",
            "amount": "150000.00",
            "currency": Currency.ARS,
            "date": today.isoformat(),
        }

        response = authenticated_client.post(income_url, income_data_ars)
        assert response.status_code == 302

        income_data_usd = {
            "category": category.pk,
            "description": "Freelance",
            "amount": "200.00",
            "currency": Currency.USD,
            "exchange_rate": "1200.00",
            "date": today.isoformat(),
        }

        response = authenticated_client.post(income_url, income_data_usd)
        assert response.status_code == 302

        incomes = Income.objects.filter(user=user)
        assert incomes.count() == 2

        from django.db.models import Sum

        total_ars = incomes.aggregate(total=Sum("amount_ars"))["total"]
        assert total_ars == Decimal("390000.00")

    def test_complete_savings_journey(self, authenticated_client, user):
        """
        Simula journey completo de metas de ahorro:
        1. Crear meta de ahorro
        2. Agregar depÃ³sitos
        3. Hacer retiro
        4. Completar meta
        """
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields["icon"].choices)
        color_choices = list(temp_form.fields["color"].choices)

        valid_icon = icon_choices[0][0] if icon_choices else "bi-piggy-bank"
        valid_color = color_choices[0][0] if color_choices else "green"

        create_url = reverse("savings:create")
        saving_data = {
            "name": "Fondo de emergencia",
            "target_amount": "100000.00",
            "currency": "ARS",
            "icon": valid_icon,
            "color": valid_color,
        }

        response = authenticated_client.post(create_url, saving_data)
        assert response.status_code == 302

        saving = Saving.objects.get(name="Fondo de emergencia", user=user)
        assert saving.target_amount == Decimal("100000.00")
        assert saving.current_amount == Decimal("0")
        assert saving.status == SavingStatus.ACTIVE

        movement_url = reverse("savings:add_movement", kwargs={"pk": saving.pk})

        response = authenticated_client.post(
            movement_url,
            {
                "type": "DEPOSIT",
                "amount": "30000.00",
            },
        )
        assert response.status_code == 302

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("30000.00")
        assert saving.progress_percentage == 30

        response = authenticated_client.post(
            movement_url,
            {
                "type": "DEPOSIT",
                "amount": "40000.00",
            },
        )
        assert response.status_code == 302

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("70000.00")
        assert saving.progress_percentage == 70

        response = authenticated_client.post(
            movement_url,
            {
                "type": "WITHDRAWAL",
                "amount": "10000.00",
            },
        )
        assert response.status_code == 302

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("60000.00")

        response = authenticated_client.post(
            movement_url,
            {
                "type": "DEPOSIT",
                "amount": "50000.00",
            },
        )
        assert response.status_code == 302

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("110000.00")
        assert saving.status == SavingStatus.COMPLETED
        assert saving.progress_percentage >= 100
