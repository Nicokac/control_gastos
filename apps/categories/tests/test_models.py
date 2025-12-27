"""
Tests para el modelo Category.
"""

import pytest
from decimal import Decimal

from apps.categories.models import Category
from apps.core.constants import CategoryType


@pytest.mark.django_db
class TestCategoryModel:
    """Tests para el modelo Category."""

    def test_create_expense_category(self, user):
        """Verifica creación de categoría de gasto."""
        category = Category.objects.create(
            name='Alimentación',
            type=CategoryType.EXPENSE,
            user=user,
            icon='bi-cart',
            color='#FF5733'
        )
        
        assert category.pk is not None
        assert category.name == 'Alimentación'
        assert category.type == CategoryType.EXPENSE
        assert category.user == user
        assert category.is_system is False

    def test_create_income_category(self, user):
        """Verifica creación de categoría de ingreso."""
        category = Category.objects.create(
            name='Salario',
            type=CategoryType.INCOME,
            user=user
        )
        
        assert category.type == CategoryType.INCOME

    def test_create_system_category(self):
        """Verifica creación de categoría de sistema (sin usuario)."""
        category = Category.objects.create(
            name='Otros',
            type=CategoryType.EXPENSE,
            user=None,
            is_system=True
        )
        
        assert category.is_system is True
        assert category.user is None

    def test_category_str(self, user):
        """Verifica representación string."""
        category = Category.objects.create(
            name='Transporte',
            type=CategoryType.EXPENSE,
            user=user
        )
        
        assert str(category) == 'Transporte'

    def test_category_default_values(self, user):
        """Verifica valores por defecto."""
        category = Category.objects.create(
            name='Test',
            type=CategoryType.EXPENSE,
            user=user
        )
        
        assert category.is_system is False
        assert category.is_active is True

    def test_category_soft_delete(self, expense_category):
        """Verifica soft delete de categoría."""
        expense_category.soft_delete()
        
        assert expense_category.is_active is False
        assert expense_category.deleted_at is not None

    def test_category_timestamps(self, user):
        """Verifica que se creen los timestamps."""
        category = Category.objects.create(
            name='Test',
            type=CategoryType.EXPENSE,
            user=user
        )
        
        assert category.created_at is not None
        assert category.updated_at is not None

    def test_category_unique_name_per_user(self, user):
        """Verifica que el nombre sea único por usuario y tipo."""
        Category.objects.create(
            name='Duplicada',
            type=CategoryType.EXPENSE,
            user=user
        )
        
        # Intentar crear otra con el mismo nombre debería fallar
        with pytest.raises(Exception):
            Category.objects.create(
                name='Duplicada',
                type=CategoryType.EXPENSE,
                user=user
            )

    def test_same_name_different_type_allowed(self, user):
        """Verifica que el mismo nombre con diferente tipo es permitido."""
        Category.objects.create(
            name='Otros',
            type=CategoryType.EXPENSE,
            user=user
        )
        
        # Mismo nombre pero tipo INCOME debería funcionar
        category2 = Category.objects.create(
            name='Otros',
            type=CategoryType.INCOME,
            user=user
        )
        
        assert category2.pk is not None

    def test_same_name_different_user_allowed(self, user, other_user):
        """Verifica que el mismo nombre con diferente usuario es permitido."""
        Category.objects.create(
            name='Personal',
            type=CategoryType.EXPENSE,
            user=user
        )
        
        category2 = Category.objects.create(
            name='Personal',
            type=CategoryType.EXPENSE,
            user=other_user
        )
        
        assert category2.pk is not None


@pytest.mark.django_db
class TestCategoryQuerySet:
    """Tests para el QuerySet de Category."""

    def test_filter_by_type_expense(self, user, expense_category, income_category):
        """Verifica filtro por tipo gasto."""
        expenses = Category.objects.filter(user=user, type=CategoryType.EXPENSE)
        
        assert expense_category in expenses
        assert income_category not in expenses

    def test_filter_by_type_income(self, user, expense_category, income_category):
        """Verifica filtro por tipo ingreso."""
        incomes = Category.objects.filter(user=user, type=CategoryType.INCOME)
        
        assert income_category in incomes
        assert expense_category not in incomes

    def test_user_categories_excludes_other_users(self, user, other_user, expense_category_factory):
        """Verifica que un usuario no ve categorías de otro."""
        cat_user1 = expense_category_factory(user, name='Cat User 1')
        cat_user2 = expense_category_factory(other_user, name='Cat User 2')
        
        user_categories = Category.objects.filter(user=user)
        
        assert cat_user1 in user_categories
        assert cat_user2 not in user_categories

    def test_system_categories_visible_to_all(self, user, system_expense_category):
        """Verifica que categorías de sistema son accesibles."""
        # Las categorías de sistema tienen user=None
        system_cats = Category.objects.filter(is_system=True)
        
        assert system_expense_category in system_cats