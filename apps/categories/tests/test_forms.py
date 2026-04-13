"""
Tests para los formularios de Category.
"""

import pytest

from apps.categories.forms import CategoryForm
from apps.core.constants import CategoryType


@pytest.mark.django_db
class TestCategoryForm:
    """Tests para CategoryForm."""

    def test_valid_expense_category(self, user):
        """Verifica formulario válido para categoría de gasto."""
        form = CategoryForm(
            data={
                "name": "Alimentación",
                "type": CategoryType.EXPENSE,
                "icon": "bi-cart",
                "color": "#FF5733",
            }
        )
        form.instance.user = user

        assert form.is_valid()

    def test_valid_income_category(self, user):
        """Verifica formulario válido para categoría de ingreso."""
        form = CategoryForm(
            data={
                "name": "Salario",
                "type": CategoryType.INCOME,
                "icon": "bi-cash",
                "color": "#28A745",
            }
        )
        form.instance.user = user

        assert form.is_valid()

    def test_name_required(self, user):
        """Verifica que el nombre sea requerido."""
        form = CategoryForm(
            data={
                "name": "",
                "type": CategoryType.EXPENSE,
            }
        )
        form.instance.user = user

        assert not form.is_valid()
        assert "name" in form.errors

    def test_type_required(self, user):
        """Verifica que el tipo sea requerido."""
        form = CategoryForm(
            data={
                "name": "Test",
                "type": "",
            }
        )
        form.instance.user = user

        assert not form.is_valid()
        assert "type" in form.errors

    def test_name_max_length(self, user):
        """Verifica longitud máxima del nombre."""
        form = CategoryForm(
            data={
                "name": "A" * 256,
                "type": CategoryType.EXPENSE,
            }
        )
        form.instance.user = user

        assert not form.is_valid()
        assert "name" in form.errors

    def test_valid_color_format(self, user):
        """Verifica formato de color válido."""
        form = CategoryForm(
            data={
                "name": "Test",
                "type": CategoryType.EXPENSE,
                "color": "#FF5733",
            }
        )
        form.instance.user = user

        assert form.is_valid()

    def test_default_icon(self, user):
        """Verifica ícono por defecto."""
        form = CategoryForm(
            data={
                "name": "Test",
                "type": CategoryType.EXPENSE,
            }
        )
        form.instance.user = user

        assert form.is_valid()

    def test_save_creates_category(self, user):
        """Verifica que save() cree la categoría."""
        form = CategoryForm(
            data={
                "name": "Nueva Categoría",
                "type": CategoryType.EXPENSE,
                "icon": "bi-tag",
                "color": "#6C757D",
            }
        )
        form.instance.user = user

        assert form.is_valid()

        category = form.save(commit=False)
        category.user = user
        category.save()

        assert category.pk is not None
        assert category.name == "Nueva Categoría"


@pytest.mark.django_db
class TestCategoryFormEdit:
    """Tests para edición de categorías."""

    def test_edit_category_name(self, expense_category):
        """Verifica edición del nombre."""
        form = CategoryForm(
            data={
                "name": "Nombre Editado",
                "type": expense_category.type,
                "icon": expense_category.icon or "bi-tag",
                "color": expense_category.color or "#000000",
            },
            instance=expense_category,
        )

        assert form.is_valid(), form.errors

        saved_cat = form.save()
        assert saved_cat.name == "Nombre Editado"

    def test_edit_category_icon(self, expense_category):
        """Verifica edición del icono."""
        form = CategoryForm(
            data={
                "name": expense_category.name,
                "type": expense_category.type,
                "icon": "bi-star",
                "color": expense_category.color or "#000000",
            },
            instance=expense_category,
        )

        assert form.is_valid(), form.errors

        saved_cat = form.save()
        assert saved_cat.icon == "bi-star"


@pytest.mark.django_db
class TestCategoryFormDuplicates:
    """Tests para validación de duplicados en CategoryForm."""

    def test_same_name_different_type_valid(self, user, expense_category):
        """Verifica que mismo nombre con diferente tipo sea válido."""
        form = CategoryForm(
            data={
                "name": expense_category.name,
                "type": CategoryType.INCOME,
                "icon": "bi-cash",
                "color": "#00FF00",
            }
        )
        form.instance.user = user

        assert form.is_valid(), form.errors

    def test_edit_category_keeps_same_name_valid(self, expense_category):
        """Verifica que editar categoría con mismo nombre sea válido."""
        form = CategoryForm(
            data={
                "name": expense_category.name,
                "type": expense_category.type,
                "icon": "bi-star",
                "color": expense_category.color or "#000000",
            },
            instance=expense_category,
        )

        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestCategoryFormCleanedData:
    """Tests para cleaned_data de CategoryForm."""

    def test_cleaned_data_types(self, user):
        """Verifica tipos en cleaned_data."""
        form = CategoryForm(
            data={
                "name": "Nueva Categoría",
                "type": CategoryType.EXPENSE,
                "icon": "bi-cart",
                "color": "#FF5733",
            }
        )
        form.instance.user = user

        assert form.is_valid(), form.errors

        assert isinstance(form.cleaned_data["name"], str)
        assert form.cleaned_data["color"].startswith("#")

    def test_name_is_stripped(self, user):
        """Verifica que el nombre se limpie de espacios."""
        form = CategoryForm(
            data={
                "name": "  Categoría con espacios  ",
                "type": CategoryType.EXPENSE,
                "icon": "bi-tag",
                "color": "#000000",
            }
        )
        form.instance.user = user

        assert form.is_valid(), form.errors

        cleaned_name = form.cleaned_data["name"]
        assert cleaned_name == cleaned_name.strip()

    def test_icon_choices_include_extended_catalog(self, user):
        """Verifica que el formulario ofrezca un catálogo amplio de iconos."""
        form = CategoryForm(user=user)

        values = [value for value, _label in form.fields["icon"].choices]

        assert "" in values
        assert "bi-cash" in values
        assert "bi-graph-up-arrow" in values
        assert len(values) >= 31
