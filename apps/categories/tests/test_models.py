"""
Tests para el modelo Category.
"""

from django.core.exceptions import ValidationError

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType


@pytest.mark.django_db
class TestCategoryModel:
    """Tests para el modelo Category."""

    def test_create_expense_category(self, user):
        """Verifica creación de categoría de gasto."""
        category = Category.objects.create(
            name="Alimentación",
            type=CategoryType.EXPENSE,
            user=user,
            icon="bi-cart",
            color="#FF5733",
        )

        assert category.pk is not None
        assert category.name == "Alimentación"
        assert category.type == CategoryType.EXPENSE
        assert category.user == user
        assert category.is_system is False

    def test_create_income_category(self, user):
        """Verifica creación de categoría de ingreso."""
        category = Category.objects.create(name="Salario", type=CategoryType.INCOME, user=user)

        assert category.type == CategoryType.INCOME

    def test_create_system_category(self):
        """Verifica creación de categoría de sistema (sin usuario)."""
        category = Category.objects.create(
            name="Otros", type=CategoryType.EXPENSE, user=None, is_system=True
        )

        assert category.is_system is True
        assert category.user is None

    def test_category_str(self, user):
        """Verifica representación string."""
        category = Category.objects.create(name="Transporte", type=CategoryType.EXPENSE, user=user)

        # El __str__ incluye el tipo
        assert "Transporte" in str(category)

    def test_category_default_values(self, user):
        """Verifica valores por defecto."""
        category = Category.objects.create(name="Test", type=CategoryType.EXPENSE, user=user)

        assert category.is_system is False

    def test_category_timestamps(self, user):
        """Verifica que se creen los timestamps."""
        category = Category.objects.create(name="Test", type=CategoryType.EXPENSE, user=user)

        assert category.created_at is not None
        assert category.updated_at is not None

    def test_category_unique_name_per_user(self, user):
        """Verifica que el nombre sea único por usuario y tipo."""
        Category.objects.create(name="Duplicada", type=CategoryType.EXPENSE, user=user)

        # Lanza ValidationError porque full_clean() se llama en save()
        with pytest.raises(ValidationError):
            Category.objects.create(name="Duplicada", type=CategoryType.EXPENSE, user=user)

    def test_same_name_different_type_allowed(self, user):
        """Verifica que el mismo nombre con diferente tipo es permitido."""
        Category.objects.create(name="Otros", type=CategoryType.EXPENSE, user=user)

        # Mismo nombre pero tipo INCOME debería funcionar
        category2 = Category.objects.create(name="Otros", type=CategoryType.INCOME, user=user)

        assert category2.pk is not None

    def test_same_name_different_user_allowed(self, user, other_user):
        """Verifica que el mismo nombre con diferente usuario es permitido."""
        Category.objects.create(name="Personal", type=CategoryType.EXPENSE, user=user)

        category2 = Category.objects.create(
            name="Personal", type=CategoryType.EXPENSE, user=other_user
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
        cat_user1 = expense_category_factory(user, name="Cat User 1")
        cat_user2 = expense_category_factory(other_user, name="Cat User 2")

        user_categories = Category.objects.filter(user=user)

        assert cat_user1 in user_categories
        assert cat_user2 not in user_categories

    def test_system_categories_visible_to_all(self, user, system_expense_category):
        """Verifica que categorías de sistema son accesibles."""
        # Las categorías de sistema tienen user=None
        system_cats = Category.objects.filter(is_system=True)

        assert system_expense_category in system_cats


@pytest.mark.django_db
class TestCategoryHierarchy:
    """Tests para la jerarquía grupo → subcategoría."""

    def test_group_has_no_parent(self, system_expense_group):
        assert system_expense_group.parent is None
        assert system_expense_group.is_group is True
        assert system_expense_group.is_subcategory is False

    def test_subcategory_has_parent(self, expense_category):
        assert expense_category.parent is not None
        assert expense_category.is_group is False
        assert expense_category.is_subcategory is True

    def test_cannot_nest_beyond_two_levels(self, user, expense_category):
        with pytest.raises(ValidationError):
            Category.objects.create(
                name="Nivel 3",
                type=CategoryType.EXPENSE,
                user=user,
                parent=expense_category,
            )

    def test_parent_must_match_type(self, user, system_income_group):
        with pytest.raises(ValidationError):
            Category.objects.create(
                name="Tipo incorrecto",
                type=CategoryType.EXPENSE,
                user=user,
                parent=system_income_group,
            )

    def test_get_user_categories_returns_only_subcategories(
        self, user, expense_category, system_expense_group
    ):
        result = list(Category.get_expense_categories(user))
        assert expense_category in result
        assert system_expense_group not in result

    def test_get_groups_returns_only_groups(self, user, expense_category, system_expense_group):
        result = list(Category.get_groups(user, CategoryType.EXPENSE))
        assert system_expense_group in result
        assert expense_category not in result

    def test_user_can_create_own_group(self, user):
        group = Category.objects.create(
            name="Mi grupo",
            type=CategoryType.EXPENSE,
            user=user,
            is_system=False,
            parent=None,
        )
        assert group.is_group is True
        assert group.user == user

    def test_delete_group_with_subcategories_is_protected(self, user, expense_category):
        from django.db import models as django_models

        with pytest.raises(django_models.ProtectedError):
            expense_category.parent.delete()


@pytest.mark.django_db
class TestGetCategoriesByGroup:
    """Tests para el método get_categories_by_group."""

    def test_returns_list_of_dicts(self, user, expense_category):
        result = Category.get_categories_by_group(user, CategoryType.EXPENSE)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "group" in result[0]
        assert "subcategories" in result[0]

    def test_subcategory_in_correct_group(self, user, expense_category):
        result = Category.get_categories_by_group(user, CategoryType.EXPENSE)
        all_subs = [sub for entry in result for sub in entry["subcategories"]]
        assert expense_category in all_subs

    def test_groups_without_subcategories_excluded(self, user, system_expense_group):
        result = Category.get_categories_by_group(user, CategoryType.EXPENSE)
        for entry in result:
            assert len(entry["subcategories"]) > 0

    def test_does_not_include_other_user_subcategories(
        self, user, other_user, expense_category_factory
    ):
        expense_category_factory(other_user, name="Ajena del otro")
        result = Category.get_categories_by_group(user, CategoryType.EXPENSE)
        all_subs = [sub for entry in result for sub in entry["subcategories"]]
        names = [s.name for s in all_subs]
        assert "Ajena del otro" not in names

    def test_filters_by_type(self, user, expense_category, income_category):
        expense_result = Category.get_categories_by_group(user, CategoryType.EXPENSE)
        income_result = Category.get_categories_by_group(user, CategoryType.INCOME)
        expense_subs = [sub for e in expense_result for sub in e["subcategories"]]
        income_subs = [sub for e in income_result for sub in e["subcategories"]]
        assert expense_category in expense_subs
        assert income_category not in expense_subs
        assert income_category in income_subs
        assert expense_category not in income_subs
