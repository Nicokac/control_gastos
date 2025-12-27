"""
Tests para los managers personalizados.
"""

import pytest
from decimal import Decimal
from django.utils import timezone

from apps.categories.models import Category
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.core.constants import CategoryType, Currency


@pytest.mark.django_db
class TestSoftDeleteManager:
    """Tests para SoftDeleteManager."""

    def test_objects_excludes_soft_deleted(self, user, expense_category, expense_factory):
        """Verifica que objects excluya registros soft-deleted."""
        # Crear gasto activo
        active_expense = expense_factory(user, expense_category, description='Activo')
        
        # Crear gasto y eliminarlo
        deleted_expense = expense_factory(user, expense_category, description='Eliminado')
        deleted_expense.soft_delete()
        
        # objects NO debe incluir el eliminado
        active_expenses = Expense.objects.filter(user=user)
        
        assert active_expense in active_expenses
        assert deleted_expense not in active_expenses

    def test_all_objects_includes_soft_deleted(self, user, expense_category, expense_factory):
        """Verifica que all_objects incluya registros soft-deleted."""
        # Crear gasto activo
        active_expense = expense_factory(user, expense_category, description='Activo')
        
        # Crear gasto y eliminarlo
        deleted_expense = expense_factory(user, expense_category, description='Eliminado')
        deleted_expense.soft_delete()
        
        # all_objects DEBE incluir ambos
        all_expenses = Expense.all_objects.filter(user=user)
        
        assert active_expense in all_expenses
        assert deleted_expense in all_expenses

    def test_soft_delete_sets_is_active_false(self, expense):
        """Verifica que soft_delete setee is_active=False."""
        assert expense.is_active is True
        
        expense.soft_delete()
        
        assert expense.is_active is False

    def test_soft_delete_sets_deleted_at(self, expense):
        """Verifica que soft_delete setee deleted_at."""
        assert expense.deleted_at is None
        
        expense.soft_delete()
        
        assert expense.deleted_at is not None

    def test_soft_deleted_still_in_database(self, user, expense_category, expense_factory):
        """Verifica que soft-delete no elimine físicamente."""
        expense = expense_factory(user, expense_category)
        expense_id = expense.pk
        
        expense.soft_delete()
        
        # Debe existir en all_objects
        assert Expense.all_objects.filter(pk=expense_id).exists()
        
        # No debe existir en objects (manager default)
        assert not Expense.objects.filter(pk=expense_id).exists()

    def test_count_excludes_soft_deleted(self, user, expense_category, expense_factory):
        """Verifica que count() excluya soft-deleted."""
        expense_factory(user, expense_category, description='Exp 1')
        expense_factory(user, expense_category, description='Exp 2')
        exp3 = expense_factory(user, expense_category, description='Exp 3')
        
        exp3.soft_delete()
        
        # Count debe ser 2, no 3
        count = Expense.objects.filter(user=user).count()
        assert count == 2

    def test_aggregate_excludes_soft_deleted(self, user, expense_category, expense_factory):
        """Verifica que aggregate excluya soft-deleted."""
        from django.db.models import Sum
        
        expense_factory(user, expense_category, amount=Decimal('100.00'))
        expense_factory(user, expense_category, amount=Decimal('200.00'))
        exp3 = expense_factory(user, expense_category, amount=Decimal('300.00'))
        
        exp3.soft_delete()
        
        # Sum debe ser 300, no 600
        total = Expense.objects.filter(user=user).aggregate(
            total=Sum('amount_ars')
        )['total']
        
        assert total == Decimal('300.00')


@pytest.mark.django_db
class TestSoftDeleteManagerCategory:
    """Tests de SoftDeleteManager específicos para Category."""

    def test_category_soft_delete(self, user, expense_category):
        """Verifica soft delete en categorías."""
        cat_id = expense_category.pk
        
        expense_category.soft_delete()
        
        # No debe aparecer en objects
        assert not Category.objects.filter(pk=cat_id).exists()
        
        # Debe aparecer en all_objects
        assert Category.all_objects.filter(pk=cat_id).exists()

    def test_user_sees_only_active_categories(self, user, expense_category_factory):
        """Verifica que usuario solo vea categorías activas."""
        cat1 = expense_category_factory(user, name='Cat 1')
        cat2 = expense_category_factory(user, name='Cat 2')
        cat3 = expense_category_factory(user, name='Cat 3')
        
        cat2.soft_delete()
        
        user_cats = Category.objects.filter(user=user)
        
        assert cat1 in user_cats
        assert cat2 not in user_cats
        assert cat3 in user_cats


@pytest.mark.django_db
class TestSoftDeleteManagerIncome:
    """Tests de SoftDeleteManager específicos para Income."""

    def test_income_soft_delete(self, user, income_category, income_factory):
        """Verifica soft delete en ingresos."""
        income = income_factory(user, income_category)
        income_id = income.pk
        
        income.soft_delete()
        
        assert not Income.objects.filter(pk=income_id).exists()
        assert Income.all_objects.filter(pk=income_id).exists()

    def test_monthly_income_excludes_deleted(self, user, income_category, income_factory, today):
        """Verifica que suma mensual excluya eliminados."""
        from django.db.models import Sum
        
        income_factory(user, income_category, amount=Decimal('50000.00'), date=today)
        income2 = income_factory(user, income_category, amount=Decimal('30000.00'), date=today)
        
        income2.soft_delete()
        
        total = Income.objects.filter(
            user=user,
            date__month=today.month,
            date__year=today.year
        ).aggregate(total=Sum('amount_ars'))['total']
        
        assert total == Decimal('50000.00')