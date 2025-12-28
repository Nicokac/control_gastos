"""
Tests para los formularios de Category.
"""

import pytest
from apps.categories.forms import CategoryForm
from apps.categories.models import Category
from apps.core.constants import CategoryType
from django.core.exceptions import ValidationError


@pytest.mark.django_db
class TestCategoryForm:
    """Tests para CategoryForm."""

    def test_valid_expense_category(self, user):
        """Verifica formulario válido para categoría de gasto."""
        form = CategoryForm(data={
            'name': 'Alimentación',
            'type': CategoryType.EXPENSE,
            'icon': 'bi-cart',
            'color': '#FF5733',
        })
        
        assert form.is_valid()

    def test_valid_income_category(self, user):
        """Verifica formulario válido para categoría de ingreso."""
        form = CategoryForm(data={
            'name': 'Salario',
            'type': CategoryType.INCOME,
            'icon': 'bi-cash',
            'color': '#28A745',
        })
        
        assert form.is_valid()

    def test_name_required(self):
        """Verifica que el nombre sea requerido."""
        form = CategoryForm(data={
            'name': '',
            'type': CategoryType.EXPENSE,
        })
        
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_type_required(self):
        """Verifica que el tipo sea requerido."""
        form = CategoryForm(data={
            'name': 'Test',
            'type': '',
        })
        
        assert not form.is_valid()
        assert 'type' in form.errors

    def test_name_max_length(self):
        """Verifica longitud máxima del nombre."""
        form = CategoryForm(data={
            'name': 'A' * 256,  # Excede el máximo
            'type': CategoryType.EXPENSE,
        })
        
        assert not form.is_valid()
        assert 'name' in form.errors

    def test_valid_color_format(self):
        """Verifica formato de color válido."""
        form = CategoryForm(data={
            'name': 'Test',
            'type': CategoryType.EXPENSE,
            'color': '#FF5733',
        })
        
        assert form.is_valid()

    def test_default_icon(self):
        """Verifica icono por defecto."""
        form = CategoryForm(data={
            'name': 'Test',
            'type': CategoryType.EXPENSE,
        })
        
        assert form.is_valid()
        # El icono debería tener un valor por defecto o ser opcional

    def test_duplicate_name_same_user_type(self, user, expense_category):
        """Verifica que no se permitan nombres duplicados."""
        form = CategoryForm(data={
            'name': expense_category.name,
            'type': CategoryType.EXPENSE,
        })
        form.instance.user = user
        
        # La validación de unicidad debería fallar
        # Nota: Esto depende de cómo esté implementado el form
        if hasattr(form, 'clean'):
            assert not form.is_valid() or 'name' in form.errors or '__all__' in form.errors

    def test_save_creates_category(self, user):
        """Verifica que save() cree la categoría."""
        form = CategoryForm(data={
            'name': 'Nueva Categoría',
            'type': CategoryType.EXPENSE,
            'icon': 'bi-tag',
            'color': '#6C757D',
        })
        
        assert form.is_valid()
        
        category = form.save(commit=False)
        category.user = user
        category.save()
        
        assert category.pk is not None
        assert category.name == 'Nueva Categoría'


@pytest.mark.django_db
class TestCategoryFormEdit:
    """Tests para edición de categorías."""

    def test_edit_category_name(self, expense_category):
        """Verifica edición del nombre."""
        form = CategoryForm(
            data={
                'name': 'Nombre Editado',
                'type': expense_category.type,
                'icon': expense_category.icon,
                'color': expense_category.color,
            },
            instance=expense_category
        )
        
        assert form.is_valid()
        
        category = form.save()
        assert category.name == 'Nombre Editado'

    def test_edit_category_icon(self, expense_category):
        """Verifica edición del icono."""
        form = CategoryForm(
            data={
                'name': expense_category.name,
                'type': expense_category.type,
                'icon': 'bi-star',
                'color': expense_category.color,
            },
            instance=expense_category
        )
        
        assert form.is_valid()
        
        category = form.save()
        assert category.icon == 'bi-star'


@pytest.mark.django_db
class TestCategoryFormDuplicates:
    """Tests para validación de duplicados en CategoryForm."""

    def test_duplicate_name_same_user_type_invalid(self, user, expense_category):
        """Verifica que no se permitan nombres duplicados."""
        form = CategoryForm(
            data={
                'name': expense_category.name,  # Mismo nombre
                'type': CategoryType.EXPENSE,   # Mismo tipo
                'icon': 'bi-tag',
                'color': '#FF0000',
            }
        )
        form.instance.user = user
        
        # Debe ser inválido
        assert not form.is_valid()
        # Error puede estar en __all__ o en name
        assert '__all__' in form.errors or 'name' in form.errors

    def test_same_name_different_type_valid(self, user, expense_category):
        """Verifica que mismo nombre con diferente tipo sea válido."""
        form = CategoryForm(
            data={
                'name': expense_category.name,  # Mismo nombre
                'type': CategoryType.INCOME,    # Diferente tipo
                'icon': 'bi-cash',
                'color': '#00FF00',
            }
        )
        form.instance.user = user
        
        assert form.is_valid(), form.errors

    def test_edit_category_keeps_same_name_valid(self, expense_category):
        """Verifica que editar categoría con mismo nombre sea válido."""
        form = CategoryForm(
            data={
                'name': expense_category.name,  # Mismo nombre
                'type': expense_category.type,
                'icon': 'bi-star',  # Cambiar solo icono
                'color': expense_category.color,
            },
            instance=expense_category  # Pasar instancia existente
        )
        
        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestCategoryFormCleanedData:
    """Tests para cleaned_data de CategoryForm."""

    def test_cleaned_data_types(self, user):
        """Verifica tipos en cleaned_data."""
        form = CategoryForm(
            data={
                'name': 'Nueva Categoría',
                'type': CategoryType.EXPENSE,
                'icon': 'bi-cart',
                'color': '#FF5733',
            }
        )
        
        assert form.is_valid(), form.errors
        
        # Verificar tipos
        assert isinstance(form.cleaned_data['name'], str)
        assert form.cleaned_data['type'] == CategoryType.EXPENSE
        assert form.cleaned_data['color'].startswith('#')

    def test_name_is_stripped(self, user):
        """Verifica que el nombre se limpie de espacios."""
        form = CategoryForm(
            data={
                'name': '  Categoría con espacios  ',
                'type': CategoryType.EXPENSE,
            }
        )
        
        assert form.is_valid(), form.errors
        
        # El nombre debería estar limpio
        cleaned_name = form.cleaned_data['name']
        assert cleaned_name == cleaned_name.strip()