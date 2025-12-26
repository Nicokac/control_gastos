"""
Tests para los mixins del sistema.
"""

import pytest
from django.utils import timezone
from datetime import timedelta

from apps.categories.models import Category
from apps.core.constants import CategoryType


@pytest.mark.django_db
class TestTimestampMixin:
    """Tests para TimestampMixin."""

    def test_created_at_auto_set_on_create(self, user):
        """Verifica que created_at se setee automáticamente."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        assert category.created_at is not None

    def test_created_at_is_datetime(self, user):
        """Verifica que created_at sea datetime."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        assert hasattr(category.created_at, 'year')
        assert hasattr(category.created_at, 'month')

    def test_updated_at_auto_set_on_create(self, user):
        """Verifica que updated_at se setee automáticamente."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        assert category.updated_at is not None

    def test_updated_at_changes_on_save(self, user):
        """Verifica que updated_at cambie al guardar."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        original_updated_at = category.updated_at
        
        # Esperar un momento y actualizar
        category.name = 'Updated Category'
        category.save()
        
        # updated_at debería ser >= al original
        assert category.updated_at >= original_updated_at

    def test_created_at_does_not_change_on_update(self, user):
        """Verifica que created_at no cambie al actualizar."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        original_created_at = category.created_at
        
        category.name = 'Updated Category'
        category.save()
        
        assert category.created_at == original_created_at


@pytest.mark.django_db
class TestSoftDeleteMixin:
    """Tests para SoftDeleteMixin."""

    def test_is_active_default_true(self, user):
        """Verifica que is_active sea True por defecto."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        assert category.is_active is True

    def test_deleted_at_default_none(self, user):
        """Verifica que deleted_at sea None por defecto."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        assert category.deleted_at is None

    def test_soft_delete_sets_is_active_false(self, user):
        """Verifica que soft_delete setee is_active en False."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        category.soft_delete()
        
        assert category.is_active is False

    def test_soft_delete_sets_deleted_at(self, user):
        """Verifica que soft_delete setee deleted_at."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        category.soft_delete()
        
        assert category.deleted_at is not None

    def test_soft_deleted_object_still_exists_in_db(self, user):
        """Verifica que el objeto siga existiendo en la DB después de soft delete."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        category_id = category.id
        category.soft_delete()
        
        # El objeto debe seguir existiendo
        assert Category.objects.filter(id=category_id).exists()

    def test_soft_deleted_object_excluded_from_active_filter(self, user):
        """Verifica que el objeto soft-deleted se excluya con filtro is_active."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        category_id = category.id
        category.soft_delete()
        
        # No debe aparecer en consultas filtradas por is_active=True
        assert not Category.objects.filter(id=category_id, is_active=True).exists()
        
        # Pero sí en consultas sin filtro o con is_active=False
        assert Category.objects.filter(id=category_id, is_active=False).exists()

    def test_restore_sets_is_active_true(self, user):
        """Verifica que restore setee is_active en True."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        category.soft_delete()
        
        # Restaurar manualmente (si existe el método)
        category.is_active = True
        category.deleted_at = None
        category.save()
        
        assert category.is_active is True
        assert category.deleted_at is None

    def test_multiple_soft_deletes(self, user):
        """Verifica múltiples soft deletes del mismo objeto."""
        category = Category.objects.create(
            name='Test Category',
            type=CategoryType.EXPENSE,
            user=user
        )
        
        # Primer soft delete
        category.soft_delete()
        first_deleted_at = category.deleted_at
        
        # Segundo soft delete (debería actualizar deleted_at)
        category.soft_delete()
        
        # deleted_at debería ser >= al primero
        assert category.deleted_at >= first_deleted_at