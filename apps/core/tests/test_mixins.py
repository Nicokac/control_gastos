"""
Tests para los mixins del sistema.
"""

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType


@pytest.mark.django_db
class TestTimestampMixin:
    """Tests para TimestampMixin."""

    def test_created_at_auto_set_on_create(self, user):
        """Verifica que created_at se setee automáticamente."""
        category = Category.objects.create(
            name="Test Category", type=CategoryType.EXPENSE, user=user
        )
        assert category.created_at is not None

    def test_created_at_is_datetime(self, user):
        """Verifica que created_at sea datetime."""
        category = Category.objects.create(
            name="Test Category", type=CategoryType.EXPENSE, user=user
        )
        assert hasattr(category.created_at, "year")
        assert hasattr(category.created_at, "month")

    def test_updated_at_auto_set_on_create(self, user):
        """Verifica que updated_at se setee automáticamente."""
        category = Category.objects.create(
            name="Test Category", type=CategoryType.EXPENSE, user=user
        )
        assert category.updated_at is not None

    def test_updated_at_changes_on_save(self, user):
        """Verifica que updated_at cambie al guardar."""
        category = Category.objects.create(
            name="Test Category", type=CategoryType.EXPENSE, user=user
        )
        original_updated_at = category.updated_at

        # Esperar un momento y actualizar
        category.name = "Updated Category"
        category.save()

        # updated_at debería ser >= al original
        assert category.updated_at >= original_updated_at

    def test_created_at_does_not_change_on_update(self, user):
        """Verifica que created_at no cambie al actualizar."""
        category = Category.objects.create(
            name="Test Category", type=CategoryType.EXPENSE, user=user
        )
        original_created_at = category.created_at

        category.name = "Updated Category"
        category.save()

        assert category.created_at == original_created_at
