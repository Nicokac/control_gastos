"""
Tests para los formularios de Budget.
"""

import pytest
from decimal import Decimal
from django.utils import timezone

from apps.budgets.forms import BudgetForm
from apps.budgets.models import Budget


@pytest.mark.django_db
class TestBudgetForm:
    """Tests para BudgetForm."""

    def test_valid_budget(self, user, expense_category):
        """Verifica formulario válido para presupuesto."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
                'alert_threshold': 80,
            },
            user=user
        )
        
        assert form.is_valid(), form.errors

    def test_category_required(self, user):
        """Verifica que la categoría sea requerida."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'category' in form.errors

    def test_amount_required(self, user, expense_category):
        """Verifica que el monto sea requerido."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_negative_amount_invalid(self, user, expense_category):
        """Verifica que monto negativo sea inválido."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '-50000.00',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_zero_amount_invalid(self, user, expense_category):
        """Verifica que monto cero sea inválido."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '0',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'amount' in form.errors

    def test_alert_threshold_default(self, user, expense_category):
        """Verifica umbral de alerta por defecto."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
            },
            user=user
        )
        
        assert form.is_valid(), form.errors
        
        budget = form.save(commit=False)
        budget.user = user
        budget.save()
        
        assert budget.alert_threshold == 80

    def test_alert_threshold_range(self, user, expense_category):
        """Verifica rango válido de umbral de alerta."""
        today = timezone.now().date()
        
        # Umbral menor a 0
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
                'alert_threshold': -10,
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'alert_threshold' in form.errors

    def test_alert_threshold_over_100_invalid(self, user, expense_category):
        """Verifica que umbral mayor a 100 sea inválido."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
                'alert_threshold': 150,
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'alert_threshold' in form.errors

    def test_month_required(self, user, expense_category):
        """Verifica que el mes sea requerido."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'year': today.year,
                'amount': '50000.00',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'month' in form.errors

    def test_year_required(self, user, expense_category):
        """Verifica que el año sea requerido."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'amount': '50000.00',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'year' in form.errors

    def test_invalid_month(self, user, expense_category):
        """Verifica que mes inválido sea rechazado."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': 13,  # Mes inválido
                'year': today.year,
                'amount': '50000.00',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'month' in form.errors


@pytest.mark.django_db
class TestBudgetFormCategories:
    """Tests para filtrado de categorías en BudgetForm."""

    def test_only_expense_categories(self, user, expense_category, income_category):
        """Verifica que solo muestre categorías de gasto."""
        form = BudgetForm(user=user)
        
        category_queryset = form.fields['category'].queryset
        
        # Debe incluir categoría de gasto
        assert expense_category in category_queryset
        
        # No debe incluir categoría de ingreso
        assert income_category not in category_queryset

    def test_excludes_other_user_categories(self, user, other_user, expense_category_factory):
        """Verifica que excluya categorías de otros usuarios."""
        cat_other = expense_category_factory(other_user, name='Otra')
        
        form = BudgetForm(user=user)
        category_queryset = form.fields['category'].queryset
        
        assert cat_other not in category_queryset


@pytest.mark.django_db
class TestBudgetFormDuplicate:
    """Tests para validación de duplicados en BudgetForm."""

    def test_duplicate_budget_invalid(self, user, expense_category, budget):
        """Verifica que presupuesto duplicado sea inválido."""
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': budget.month,
                'year': budget.year,
                'amount': '60000.00',
            },
            user=user
        )
        
        assert not form.is_valid()
        assert '__all__' in form.errors or 'category' in form.errors

    def test_same_category_different_month_valid(self, user, expense_category, budget):
        """Verifica que misma categoría en diferente mes sea válido."""
        # Calcular mes diferente
        if budget.month == 12:
            new_month = 1
            new_year = budget.year + 1
        else:
            new_month = budget.month + 1
            new_year = budget.year
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': new_month,
                'year': new_year,
                'amount': '60000.00',
            },
            user=user
        )
        
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestBudgetFormSave:
    """Tests para guardado de BudgetForm."""

    def test_save_creates_budget(self, user, expense_category):
        """Verifica que save() cree el presupuesto."""
        today = timezone.now().date()
        
        # Usar mes diferente al actual para evitar duplicados
        if today.month == 12:
            test_month = 1
            test_year = today.year + 1
        else:
            test_month = today.month + 1
            test_year = today.year
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': test_month,
                'year': test_year,
                'amount': '75000.00',
                'alert_threshold': 70,
            },
            user=user
        )
        
        assert form.is_valid(), form.errors
        
        budget = form.save(commit=False)
        budget.user = user
        budget.save()
        
        assert budget.pk is not None
        assert budget.amount == Decimal('75000.00')
        assert budget.alert_threshold == 70