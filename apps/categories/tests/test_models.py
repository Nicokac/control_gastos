"""
Tests para el modelo Category.
"""

from django.core.exceptions import ValidationError

import pytest

from apps.categories.models import Category, CategoryOverride
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
class TestCategoryOverride:
    """Tests para CategoryOverride — ocultar categorías de sistema por
    usuario sin afectar a otros usuarios ni a la categoría compartida
    (DT-086, fase 1: solo ocultar)."""

    def test_crear_override_de_categoria_de_sistema(self, user, system_expense_group):
        override = CategoryOverride.objects.create(
            user=user, category=system_expense_group, is_hidden=True
        )
        assert override.pk is not None
        assert override.is_hidden is True

    def test_no_se_puede_crear_override_de_categoria_de_usuario(self, user, expense_category):
        with pytest.raises(ValidationError):
            CategoryOverride.objects.create(user=user, category=expense_category, is_hidden=True)

    def test_un_solo_override_por_usuario_y_categoria(self, user, system_expense_group):
        CategoryOverride.objects.create(user=user, category=system_expense_group, is_hidden=True)
        with pytest.raises(ValidationError):
            CategoryOverride.objects.create(
                user=user, category=system_expense_group, is_hidden=True
            )

    def test_categoria_oculta_no_aparece_en_get_groups(self, user, system_expense_group):
        CategoryOverride.objects.create(user=user, category=system_expense_group, is_hidden=True)
        result = list(Category.get_groups(user, CategoryType.EXPENSE))
        assert system_expense_group not in result

    def test_categoria_oculta_no_aparece_para_otro_usuario(
        self, user, other_user, system_expense_group
    ):
        """Ocultar es por usuario — no afecta a nadie más."""
        CategoryOverride.objects.create(user=user, category=system_expense_group, is_hidden=True)
        result = list(Category.get_groups(other_user, CategoryType.EXPENSE))
        assert system_expense_group in result

    def test_subcategoria_oculta_no_aparece_en_get_expense_categories(
        self, user, system_expense_group
    ):
        system_subcat = Category.objects.create(
            name="Sub de sistema",
            type=CategoryType.EXPENSE,
            is_system=True,
            user=None,
            parent=system_expense_group,
        )
        CategoryOverride.objects.create(user=user, category=system_subcat, is_hidden=True)

        result = list(Category.get_expense_categories(user))
        assert system_subcat not in result

    def test_no_afecta_gastos_ya_cargados_con_esa_categoria(
        self, user, expense_category_factory, expense_factory
    ):
        """Ocultar solo afecta el selector al crear — el historial sigue igual."""
        system_subcat = expense_category_factory(user=None, name="Sub de sistema 2", is_system=True)
        expense = expense_factory(user, system_subcat)
        CategoryOverride.objects.create(user=user, category=system_subcat, is_hidden=True)

        expense.refresh_from_db()
        assert expense.category_id == system_subcat.id


@pytest.mark.django_db
class TestDefaultSystemSubcategories:
    """Verifica que un usuario nuevo, sin ninguna subcategoría propia, tenga
    al menos una categoría válida disponible (DT-085) — reportado por un
    usuario real: 'Sin clasificar' y 'Sueldo' quedaron sin subcategorías de
    sistema tras la migración 0011, dejando el formulario sin opciones.

    Los tests corren con --nomigrations (ver pyproject.toml), así que los
    RunPython de datos (incluida la migración 0012 que sembró el fix) nunca
    se ejecutan acá — estos tests recrean el escenario real a propósito,
    para que sigan protegiendo la regla incluso si la data real cambia."""

    @pytest.fixture
    def sin_clasificar_vacio(self, db):
        return Category.objects.create(
            name="Sin clasificar",
            type=CategoryType.EXPENSE,
            is_system=True,
            user=None,
            parent=None,
        )

    @pytest.fixture
    def sueldo_vacio(self, db):
        return Category.objects.create(
            name="Sueldo",
            type=CategoryType.INCOME,
            is_system=True,
            user=None,
            parent=None,
        )

    def test_grupo_de_sistema_sin_subcategorias_no_ofrece_categoria_de_gasto(
        self, user, sin_clasificar_vacio
    ):
        """Reproduce el bug: sin ninguna subcategoría, el usuario no tiene
        nada para elegir al cargar un gasto."""
        result = list(Category.get_expense_categories(user))
        assert result == []

    def test_agregar_subcategoria_de_sistema_resuelve_el_bug(self, user, sin_clasificar_vacio):
        Category.objects.create(
            name="Varios",
            type=CategoryType.EXPENSE,
            is_system=True,
            user=None,
            parent=sin_clasificar_vacio,
        )
        result = list(Category.get_expense_categories(user))
        assert len(result) == 1
        assert result[0].name == "Varios"

    def test_ingresos_permite_usar_el_grupo_directo_sin_subcategorias(self, user, sueldo_vacio):
        """get_income_categories() sí incluye el grupo mismo cuando no tiene
        subcategorías (a diferencia de gastos) — por eso este bug afectaba a
        Gastos en la web/mobile, pero no de la misma forma a Ingresos."""
        result = list(Category.get_income_categories(user))
        assert result == [sueldo_vacio]

    def test_agregar_subcategoria_a_sueldo_tambien_queda_disponible(self, user, sueldo_vacio):
        Category.objects.create(
            name="Otros",
            type=CategoryType.INCOME,
            is_system=True,
            user=None,
            parent=sueldo_vacio,
        )
        result = list(Category.get_income_categories(user))
        assert len(result) == 2


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
