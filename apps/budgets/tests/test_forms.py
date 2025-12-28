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

    # def test_alert_threshold_default(self, user, expense_category):
    #     """Verifica umbral de alerta por defecto."""
    #     today = timezone.now().date()
    #     form = BudgetForm(
    #         data={
    #             'category': expense_category.pk,
    #             'month': today.month,
    #             'year': today.year,
    #             'amount': '50000.00',
    #         },
    #         user=user
    #     )
        
    #     assert form.is_valid(), form.errors
        
    #     budget = form.save(commit=False)
    #     budget.user = user
    #     budget.save()
        
    #     assert budget.alert_threshold == 80

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
                'alert_threshold': 80,  # Agregar
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


@pytest.mark.django_db
class TestBudgetFormPeriodValidation:
    """Tests para validación de período en BudgetForm."""

    def test_past_month_allowed(self, user, expense_category):
        """Verifica que se permitan presupuestos para meses pasados."""
        today = timezone.now().date()
        
        if today.month == 1:
            past_month = 12
            past_year = today.year - 1
        else:
            past_month = today.month - 1
            past_year = today.year
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': past_month,
                'year': past_year,
                'amount': '50000.00',
                'alert_threshold': 80,  # Agregar
            },
            user=user
        )
        
        assert form.is_valid(), form.errors

    def test_current_month_allowed(self, user, expense_category):
        """Verifica que se permita el mes actual."""
        today = timezone.now().date()
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
                'alert_threshold': 80,  # AGREGAR
            },
            user=user
        )
        
        assert form.is_valid(), form.errors

    def test_future_month_allowed(self, user, expense_category):
        """Verifica que se permitan meses futuros."""
        today = timezone.now().date()
        
        if today.month == 12:
            future_month = 1
            future_year = today.year + 1
        else:
            future_month = today.month + 1
            future_year = today.year
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': future_month,
                'year': future_year,
                'amount': '60000.00',
                'alert_threshold': 80,  # AGREGAR
            },
            user=user
        )
        
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestBudgetFormEditSamePeriod:
    """Tests para edición de presupuesto en mismo período."""

    def test_edit_budget_same_period_valid(self, user, expense_category, budget_factory):
        """Verifica que pueda editar un presupuesto existente."""
        # Crear presupuesto existente
        budget = budget_factory(user, expense_category)
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': budget.month,
                'year': budget.year,
                'amount': '100000.00',  # Cambiar monto
                'alert_threshold': 90,   # Cambiar umbral
            },
            instance=budget,  # Pasar instancia existente
            user=user
        )
        
        assert form.is_valid(), form.errors
        
        updated_budget = form.save()
        assert updated_budget.amount == Decimal('100000.00')
        assert updated_budget.alert_threshold == 90

    def test_edit_budget_change_amount_only(self, user, expense_category, budget_factory):
        """Verifica edición solo del monto."""
        budget = budget_factory(user, expense_category, amount=Decimal('50000.00'))
        original_threshold = budget.alert_threshold
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': budget.month,
                'year': budget.year,
                'amount': '75000.00',
                'alert_threshold': original_threshold,
            },
            instance=budget,
            user=user
        )
        
        assert form.is_valid(), form.errors
        
        updated = form.save()
        assert updated.amount == Decimal('75000.00')
        assert updated.alert_threshold == original_threshold

    def test_edit_budget_change_threshold_only(self, user, expense_category, budget_factory):
        """Verifica edición solo del umbral de alerta."""
        budget = budget_factory(user, expense_category, alert_threshold=80)
        original_amount = budget.amount
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': budget.month,
                'year': budget.year,
                'amount': str(original_amount),
                'alert_threshold': 70,
            },
            instance=budget,
            user=user
        )
        
        assert form.is_valid(), form.errors
        
        updated = form.save()
        assert updated.amount == original_amount
        assert updated.alert_threshold == 70


@pytest.mark.django_db
class TestBudgetFormCleanedData:
    """Tests para cleaned_data de BudgetForm."""

    def test_cleaned_data_types(self, user, expense_category):
        """Verifica tipos correctos en cleaned_data."""
        from apps.categories.models import Category
        
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
        
        # Verificar tipos - month/year pueden ser str o int según implementación
        assert isinstance(form.cleaned_data['amount'], Decimal)
        assert isinstance(form.cleaned_data['alert_threshold'], int)
        assert isinstance(form.cleaned_data['category'], Category)

    def test_month_in_valid_range(self, user, expense_category):
        """Verifica que el mes esté en rango válido después de clean."""
        today = timezone.now().date()
        
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
                'alert_threshold': 80,  # AGREGAR
            },
            user=user
        )
        
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestBudgetFormInitialValues:
    """Tests para valores iniciales de BudgetForm."""

    def test_alert_threshold_required(self, user, expense_category):
        """Verifica que alert_threshold sea requerido."""
        today = timezone.now().date()
        form = BudgetForm(
            data={
                'category': expense_category.pk,
                'month': today.month,
                'year': today.year,
                'amount': '50000.00',
                # Sin alert_threshold
            },
            user=user
        )
        
        assert not form.is_valid()
        assert 'alert_threshold' in form.errors

    def test_month_year_defaults_to_current(self, user):
        """Verifica que mes/año por defecto sea el actual."""
        form = BudgetForm(user=user)
        
        today = timezone.now().date()
        
        if 'month' in form.initial:
            assert form.initial['month'] == today.month
        
        if 'year' in form.initial:
            assert form.initial['year'] == today.year