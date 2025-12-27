"""
Tests para el modelo Budget.
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from django.db import IntegrityError

from apps.budgets.models import Budget
from apps.expenses.models import Expense
from apps.core.constants import Currency


@pytest.mark.django_db
class TestBudgetModel:
    """Tests para el modelo Budget."""

    def test_create_budget(self, user, expense_category):
        """Verifica creación de presupuesto."""
        today = timezone.now().date()
        budget = Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('50000.00'),
            alert_threshold=80
        )
        
        assert budget.pk is not None
        assert budget.amount == Decimal('50000.00')
        assert budget.alert_threshold == 80

    def test_budget_str(self, budget):
        """Verifica representación string."""
        result = str(budget)
        
        assert budget.category.name in result or str(budget.amount) in result

    def test_budget_default_alert_threshold(self, user, expense_category):
        """Verifica umbral de alerta por defecto."""
        today = timezone.now().date()
        budget = Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        assert budget.alert_threshold == 80

    def test_budget_soft_delete(self, budget):
        """Verifica soft delete."""
        budget.soft_delete()
        
        assert budget.is_active is False

    def test_budget_timestamps(self, budget):
        """Verifica timestamps."""
        assert budget.created_at is not None
        assert budget.updated_at is not None

    def test_budget_unique_per_category_month_year(self, user, expense_category):
        """Verifica unicidad por categoría/mes/año."""
        today = timezone.now().date()
        
        Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        with pytest.raises(Exception):
            Budget.objects.create(
                user=user,
                category=expense_category,
                month=today.month,
                year=today.year,
                amount=Decimal('20000.00')
            )


@pytest.mark.django_db
class TestBudgetCalculations:
    """Tests para cálculos de Budget."""

    def test_spent_amount_no_expenses(self, budget):
        """Verifica spent_amount sin gastos."""
        assert budget.spent_amount == Decimal('0')

    def test_spent_amount_with_expenses(self, user, expense_category, budget_factory, expense_factory):
        """Verifica spent_amount con gastos."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        expense_factory(user, expense_category, amount=Decimal('2000.00'), date=today)
        expense_factory(user, expense_category, amount=Decimal('3000.00'), date=today)
        
        assert budget.spent_amount == Decimal('5000.00')

    def test_remaining_amount(self, user, expense_category, budget_factory, expense_factory):
        """Verifica monto restante."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        expense_factory(user, expense_category, amount=Decimal('3000.00'), date=today)
        
        assert budget.remaining_amount == Decimal('7000.00')

    def test_spent_percentage_zero(self, budget):
        """Verifica porcentaje gastado en cero."""
        assert budget.spent_percentage == 0

    def test_spent_percentage_partial(self, user, expense_category, budget_factory, expense_factory):
        """Verifica porcentaje gastado parcial."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        expense_factory(user, expense_category, amount=Decimal('5000.00'), date=today)
        
        assert budget.spent_percentage == 50

    def test_spent_percentage_over_budget(self, user, expense_category, budget_factory, expense_factory):
        """Verifica porcentaje cuando se excede el presupuesto."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        expense_factory(user, expense_category, amount=Decimal('15000.00'), date=today)
        
        assert budget.spent_percentage == 150


@pytest.mark.django_db
class TestBudgetStatus:
    """Tests para el estado del presupuesto."""

    def test_is_over_budget_false(self, budget):
        """Verifica is_over_budget cuando no se excede."""
        assert budget.is_over_budget is False

    def test_is_over_budget_true(self, user, expense_category, budget_factory, expense_factory):
        """Verifica is_over_budget cuando se excede."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        expense_factory(user, expense_category, amount=Decimal('12000.00'), date=today)
        
        assert budget.is_over_budget is True

    def test_is_near_limit_false(self, budget):
        """Verifica is_near_limit cuando está lejos del límite."""
        assert budget.is_near_limit is False

    def test_is_near_limit_true(self, user, expense_category, budget_factory, expense_factory):
        """Verifica is_near_limit cuando está cerca del límite."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00'),
            alert_threshold=80
        )
        
        # 85% gastado
        expense_factory(user, expense_category, amount=Decimal('8500.00'), date=today)
        
        assert budget.is_near_limit is True
        assert budget.is_over_budget is False

    def test_status_ok(self, budget):
        """Verifica status OK."""
        assert budget.status == 'ok'

    def test_status_warning(self, user, expense_category, budget_factory, expense_factory):
        """Verifica status warning."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00'),
            alert_threshold=80
        )
        
        expense_factory(user, expense_category, amount=Decimal('8500.00'), date=today)
        
        assert budget.status == 'warning'

    def test_status_over(self, user, expense_category, budget_factory, expense_factory):
        """Verifica status over."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        expense_factory(user, expense_category, amount=Decimal('12000.00'), date=today)
        
        assert budget.status == 'over'


@pytest.mark.django_db
class TestBudgetQuerySet:
    """Tests para el QuerySet de Budget."""

    def test_filter_by_user(self, user, other_user, expense_category, expense_category_factory, budget_factory):
        """Verifica filtro por usuario."""
        budget_user1 = budget_factory(user, expense_category)
        
        other_cat = expense_category_factory(other_user, name='Other Cat')
        budget_user2 = budget_factory(other_user, other_cat)
        
        user_budgets = Budget.objects.filter(user=user)
        
        assert budget_user1 in user_budgets
        assert budget_user2 not in user_budgets

    def test_filter_by_month_year(self, user, expense_category, budget_factory, current_month, current_year):
        """Verifica filtro por mes y año."""
        budget = budget_factory(
            user,
            expense_category,
            month=current_month,
            year=current_year
        )
        
        month_budgets = Budget.objects.filter(
            user=user,
            month=current_month,
            year=current_year
        )
        
        assert budget in month_budgets

    def test_get_with_spent(self, user, expense_category, budget_factory, expense_factory):
        """Verifica método get_with_spent."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('10000.00')
        )
        
        expense_factory(user, expense_category, amount=Decimal('3000.00'), date=today)
        
        budgets = Budget.get_with_spent(user, month=today.month, year=today.year)
        
        assert budgets.count() == 1
        assert budgets.first().spent_amount == Decimal('3000.00')

@pytest.mark.django_db
class TestBudgetConstraints:
    """Tests para constraints del modelo Budget."""

    def test_unique_budget_per_category_month_year(self, user, expense_category):
        """Verifica constraint único por usuario/categoría/mes/año."""
        today = timezone.now().date()
        
        Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('5000.00')
        )
        
        # Intentar crear otro presupuesto para la misma categoría/mes/año
        with pytest.raises(IntegrityError):
            Budget.objects.create(
                user=user,
                category=expense_category,
                month=today.month,
                year=today.year,
                amount=Decimal('10000.00')
            )

    def test_same_category_different_month_allowed(self, user, expense_category):
        """Verifica que misma categoría en diferente mes sea permitido."""
        today = timezone.now().date()
        
        Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal('5000.00')
        )
        
        # Calcular próximo mes
        if today.month == 12:
            next_month = 1
            next_year = today.year + 1
        else:
            next_month = today.month + 1
            next_year = today.year
        
        # Diferente mes debería funcionar
        budget2 = Budget.objects.create(
            user=user,
            category=expense_category,
            month=next_month,
            year=next_year,
            amount=Decimal('7000.00')
        )
        
        assert budget2.pk is not None

    def test_same_month_different_category_allowed(self, user, expense_category_factory):
        """Verifica que mismo mes con diferente categoría sea permitido."""
        today = timezone.now().date()
        
        cat1 = expense_category_factory(user, name='Categoría 1')
        cat2 = expense_category_factory(user, name='Categoría 2')
        
        budget1 = Budget.objects.create(
            user=user,
            category=cat1,
            month=today.month,
            year=today.year,
            amount=Decimal('5000.00')
        )
        
        budget2 = Budget.objects.create(
            user=user,
            category=cat2,
            month=today.month,
            year=today.year,
            amount=Decimal('3000.00')
        )
        
        assert budget1.pk is not None
        assert budget2.pk is not None

    def test_same_category_month_different_user_allowed(self, user, other_user, expense_category_factory):
        """Verifica que mismo mes/categoría con diferente usuario sea permitido."""
        today = timezone.now().date()
        
        cat1 = expense_category_factory(user, name='Alimentación')
        cat2 = expense_category_factory(other_user, name='Alimentación')
        
        budget1 = Budget.objects.create(
            user=user,
            category=cat1,
            month=today.month,
            year=today.year,
            amount=Decimal('5000.00')
        )
        
        budget2 = Budget.objects.create(
            user=other_user,
            category=cat2,
            month=today.month,
            year=today.year,
            amount=Decimal('8000.00')
        )
        
        assert budget1.pk is not None
        assert budget2.pk is not None