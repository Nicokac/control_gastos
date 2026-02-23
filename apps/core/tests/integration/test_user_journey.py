"""
Tests de journey completo de usuario.
Simula el flujo real que seguiría un usuario nuevo en la aplicación.
"""

from datetime import date
from decimal import Decimal

from django.urls import reverse

import pytest

from apps.budgets.models import Budget
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
        1. Crear categoría
        2. Crear presupuesto
        3. Registrar gastos
        4. Verificar presupuesto actualizado
        5. Editar gasto
        6. Eliminar gasto
        """
        today = date.today()

        # ============================================
        # PASO 1: Crear categoría de gasto
        # ============================================
        cat_url = reverse("categories:create")
        cat_data = {
            "name": "Supermercado",
            "type": CategoryType.EXPENSE,
            "icon": "bi-cart",
            "color": "#28a745",
        }

        response = authenticated_client.post(cat_url, cat_data)
        assert response.status_code == 302, "Debería redirigir después de crear categoría"

        category = Category.objects.get(name="Supermercado", user=user)
        assert category.type == CategoryType.EXPENSE

        # ============================================
        # PASO 2: Crear presupuesto para la categoría
        # ============================================
        budget_url = reverse("budgets:create")
        budget_data = {
            "category": category.pk,
            "month": today.month,
            "year": today.year,
            "amount": "50000.00",
            "alert_threshold": 80,
        }

        response = authenticated_client.post(budget_url, budget_data)
        assert response.status_code == 302, "Debería redirigir después de crear presupuesto"

        budget = Budget.objects.get(user=user, category=category)
        assert budget.amount == Decimal("50000.00")
        assert budget.spent_amount == Decimal("0")

        # ============================================
        # PASO 3: Registrar gastos
        # ============================================
        expense_url = reverse("expenses:create")

        # Primer gasto
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

        # Segundo gasto
        expense_data_2 = {
            "category": category.pk,
            "description": "Verdulería",
            "amount": "5000.00",
            "currency": Currency.ARS,
            "date": today.isoformat(),
        }

        response = authenticated_client.post(expense_url, expense_data_2)
        assert response.status_code == 302

        # ============================================
        # PASO 4: Verificar presupuesto actualizado
        # ============================================
        budget.refresh_from_db()
        assert budget.spent_amount == Decimal("20000.00"), "Presupuesto debería sumar ambos gastos"
        assert budget.spent_percentage == Decimal("40.0"), "Porcentaje debería ser 40%"
        assert budget.remaining_amount == Decimal("30000.00")
        assert not budget.is_over_budget  # 🔧 E712
        assert not budget.is_near_limit  # 🔧 E712  (40% < 80%)

        # ============================================
        # PASO 5: Editar gasto
        # ============================================
        edit_url = reverse("expenses:update", kwargs={"pk": expense_1.pk})
        expense_data_1["description"] = "Compra semanal (editada)"
        expense_data_1["amount"] = "18000.00"

        response = authenticated_client.post(edit_url, expense_data_1)
        assert response.status_code == 302

        expense_1.refresh_from_db()
        assert expense_1.description == "Compra semanal (editada)"
        assert expense_1.amount == Decimal("18000.00")

        # Presupuesto debería actualizarse
        budget.refresh_from_db()
        assert budget.spent_amount == Decimal("23000.00")  # 18000 + 5000

        # ============================================
        # PASO 6: Eliminar gasto
        # ============================================
        expense_2 = Expense.objects.get(description="Verdulería")
        delete_url = reverse("expenses:delete", kwargs={"pk": expense_2.pk})

        response = authenticated_client.post(delete_url)
        assert response.status_code == 302

        # Verificar eliminación
        assert not Expense.objects.filter(pk=expense_2.pk).exists()

        # Presupuesto debería actualizarse
        budget.refresh_from_db()
        assert budget.spent_amount == Decimal("18000.00")  # Solo queda el primer gasto

    def test_complete_income_tracking_journey(self, authenticated_client, user):
        """
        Simula journey completo de tracking de ingresos:
        1. Crear categoría de ingreso
        2. Registrar ingresos (ARS y USD)
        3. Verificar totales
        """
        today = date.today()

        # ============================================
        # PASO 1: Crear categoría de ingreso
        # ============================================
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

        # ============================================
        # PASO 2: Registrar ingresos
        # ============================================
        income_url = reverse("income:create")

        # Ingreso en ARS
        income_data_ars = {
            "category": category.pk,
            "description": "Sueldo mensual",
            "amount": "150000.00",
            "currency": Currency.ARS,
            "date": today.isoformat(),
        }

        response = authenticated_client.post(income_url, income_data_ars)
        assert response.status_code == 302

        # Ingreso en USD
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

        # ============================================
        # PASO 3: Verificar totales
        # ============================================
        incomes = Income.objects.filter(user=user)
        assert incomes.count() == 2

        # Total en ARS
        from django.db.models import Sum

        total_ars = incomes.aggregate(total=Sum("amount_ars"))["total"]

        # 150000 + (200 * 1200) = 150000 + 240000 = 390000
        assert total_ars == Decimal("390000.00")

    def test_complete_savings_journey(self, authenticated_client, user):
        """
        Simula journey completo de metas de ahorro:
        1. Crear meta de ahorro
        2. Agregar depósitos
        3. Hacer retiro
        4. Completar meta
        """
        # Obtener valores válidos del form
        temp_form = SavingForm()
        icon_choices = list(temp_form.fields["icon"].choices)
        color_choices = list(temp_form.fields["color"].choices)

        valid_icon = icon_choices[0][0] if icon_choices else "bi-piggy-bank"
        valid_color = color_choices[0][0] if color_choices else "green"

        # ============================================
        # PASO 1: Crear meta de ahorro
        # ============================================
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

        # ============================================
        # PASO 2: Agregar depósitos
        # ============================================
        movement_url = reverse("savings:add_movement", kwargs={"pk": saving.pk})

        # Primer depósito
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

        # Segundo depósito
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

        # ============================================
        # PASO 3: Hacer retiro
        # ============================================
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

        # ============================================
        # PASO 4: Completar meta
        # ============================================
        response = authenticated_client.post(
            movement_url,
            {
                "type": "DEPOSIT",
                "amount": "50000.00",
            },
        )
        assert response.status_code == 302

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("110000.00")  # Excede meta
        assert saving.status == SavingStatus.COMPLETED
        assert saving.progress_percentage >= 100


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.django_db
class TestUserJourneyWithMultipleEntities:
    """Tests de journey con múltiples entidades relacionadas."""

    def test_monthly_budget_tracking_journey(
        self, authenticated_client, user, expense_category_factory
    ):
        """
        Simula seguimiento mensual completo:
        1. Crear múltiples categorías
        2. Crear presupuestos para cada una
        3. Registrar gastos distribuidos
        4. Verificar estado de cada presupuesto
        """
        today = date.today()

        # ============================================
        # PASO 1: Crear categorías
        # ============================================
        categories = {
            "Comida": expense_category_factory(user, name="Comida"),
            "Transporte": expense_category_factory(user, name="Transporte"),
            "Entretenimiento": expense_category_factory(user, name="Entretenimiento"),
        }

        # ============================================
        # PASO 2: Crear presupuestos
        # ============================================
        budget_url = reverse("budgets:create")
        budgets = {}

        budget_amounts = {
            "Comida": "30000.00",
            "Transporte": "15000.00",
            "Entretenimiento": "10000.00",
        }

        for cat_name, amount in budget_amounts.items():
            data = {
                "category": categories[cat_name].pk,
                "month": today.month,
                "year": today.year,
                "amount": amount,
                "alert_threshold": 80,
            }
            authenticated_client.post(budget_url, data)

            budgets[cat_name] = Budget.objects.get(user=user, category=categories[cat_name])

        # ============================================
        # PASO 3: Registrar gastos
        # ============================================
        expense_url = reverse("expenses:create")

        expenses_data = [
            ("Comida", "Almuerzo", "8000.00"),
            ("Comida", "Cena", "5000.00"),
            ("Transporte", "Uber", "3000.00"),
            ("Transporte", "Nafta", "10000.00"),
            ("Entretenimiento", "Cine", "4000.00"),
        ]

        for cat_name, description, amount in expenses_data:
            data = {
                "category": categories[cat_name].pk,
                "description": description,
                "amount": amount,
                "currency": Currency.ARS,
                "date": today.isoformat(),
            }
            authenticated_client.post(expense_url, data)

        # ============================================
        # PASO 4: Verificar presupuestos
        # ============================================

        # Comida: 13000 / 30000 = 43.3%
        budgets["Comida"].refresh_from_db()
        assert budgets["Comida"].spent_amount == Decimal("13000.00")
        assert not budgets["Comida"].is_over_budget  # 🔧 E712

        # Transporte: 13000 / 15000 = 86.7% (cerca del límite)
        budgets["Transporte"].refresh_from_db()
        assert budgets["Transporte"].spent_amount == Decimal("13000.00")
        assert budgets["Transporte"].is_near_limit  # 🔧 E712  # > 80%

        # Entretenimiento: 4000 / 10000 = 40%
        budgets["Entretenimiento"].refresh_from_db()
        assert budgets["Entretenimiento"].spent_amount == Decimal("4000.00")
        assert not budgets["Entretenimiento"].is_over_budget  # 🔧 E712
