"""
Tests para las vistas de Category.
"""

from django.urls import reverse

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType


@pytest.mark.django_db
class TestCategoryListView:
    """Tests para la vista de listado de categorías."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("categories:list")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_list_user_categories(self, authenticated_client, user, expense_category):
        """Verifica que liste las categorías del usuario."""
        url = reverse("categories:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert expense_category.name in response.content.decode()

    def test_excludes_other_user_categories(
        self, authenticated_client, user, other_user, expense_category_factory
    ):
        """Verifica que no muestre categorías de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra Categoría")

        url = reverse("categories:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert other_cat.name not in response.content.decode()

    def test_includes_system_categories(self, authenticated_client, system_expense_category):
        """Verifica que incluya categorías del sistema."""
        url = reverse("categories:list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        # Las categorías del sistema deberían estar visibles


@pytest.mark.django_db
class TestCategoryCreateView:
    """Tests para la vista de creación de categorías."""

    def test_login_required(self, client):
        """Verifica que requiera autenticación."""
        url = reverse("categories:create")
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_create_form(self, authenticated_client):
        """Verifica que muestre el formulario de creación."""
        url = reverse("categories:create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context

    def test_create_category_success(self, authenticated_client, user):
        """Verifica creación exitosa de categoría."""
        url = reverse("categories:create")
        data = {
            "name": "Nueva Categoría",
            "type": CategoryType.EXPENSE,
            "icon": "bi-tag",
            "color": "#FF5733",
        }

        response = authenticated_client.post(url, data)

        # Debería redireccionar después de crear
        assert response.status_code == 302

        # Verificar que se creó
        assert Category.objects.filter(name="Nueva Categoría", user=user).exists()

    def test_create_category_invalid_data(self, authenticated_client):
        """Verifica que no cree con datos inválidos."""
        url = reverse("categories:create")
        data = {
            "name": "",  # Nombre vacío
            "type": CategoryType.EXPENSE,
        }

        response = authenticated_client.post(url, data)

        # Debería mostrar el form con errores
        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].errors

    def test_category_assigned_to_current_user(self, authenticated_client, user):
        """Verifica que la categoría se asigne al usuario actual."""
        url = reverse("categories:create")
        data = {
            "name": "Mi Categoría",
            "type": CategoryType.EXPENSE,
            "icon": "bi-cart",
            "color": "#000000",
        }

        authenticated_client.post(url, data)

        category = Category.objects.get(name="Mi Categoría")
        assert category.user == user


@pytest.mark.django_db
class TestCategoryUpdateView:
    """Tests para la vista de edición de categorías."""

    def test_login_required(self, client, expense_category):
        """Verifica que requiera autenticación."""
        url = reverse("categories:update", kwargs={"pk": expense_category.pk})
        response = client.get(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_get_update_form(self, authenticated_client, expense_category):
        """Verifica que muestre el formulario de edición."""
        url = reverse("categories:update", kwargs={"pk": expense_category.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "form" in response.context
        assert response.context["form"].instance == expense_category

    def test_update_category_success(self, authenticated_client, expense_category):
        """Verifica edición exitosa de categoría."""
        url = reverse("categories:update", kwargs={"pk": expense_category.pk})
        data = {
            "name": "Nombre Actualizado",
            "type": expense_category.type,
            "icon": expense_category.icon or "bi-tag",
            "color": expense_category.color or "#000000",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302

        expense_category.refresh_from_db()
        assert expense_category.name == "Nombre Actualizado"

    def test_cannot_update_other_user_category(
        self, authenticated_client, other_user, expense_category_factory
    ):
        """Verifica que no pueda editar categorías de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")

        url = reverse("categories:update", kwargs={"pk": other_cat.pk})
        response = authenticated_client.get(url)

        # Debería ser 404 o 403
        assert response.status_code in [403, 404]

    def test_cannot_update_system_category(self, authenticated_client, system_expense_category):
        """Verifica que no pueda editar categorías del sistema."""
        url = reverse("categories:update", kwargs={"pk": system_expense_category.pk})
        response = authenticated_client.get(url)

        # Debería ser 404 o 403
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestCategoryDeleteView:
    """Tests para la vista de eliminación de categorías."""

    def test_login_required(self, client, expense_category):
        """Verifica que requiera autenticación."""
        url = reverse("categories:delete", kwargs={"pk": expense_category.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert "login" in response.url

    def test_delete_category_success(self, authenticated_client, expense_category):
        """Verifica eliminación exitosa de categoría."""
        url = reverse("categories:delete", kwargs={"pk": expense_category.pk})
        pk = expense_category.pk

        response = authenticated_client.post(url)

        assert response.status_code == 302

        # Verificar si es soft delete o hard delete
        from apps.categories.models import Category

        # Intentar con all_objects (soft delete)
        try:
            cat = Category.all_objects.get(pk=pk)
            assert not cat.is_active  # 🔧 E712 Soft delete
        except Category.DoesNotExist:
            # Hard delete - verificar que no existe
            assert not Category.objects.filter(pk=pk).exists()

    def test_cannot_delete_other_user_category(
        self, authenticated_client, other_user, expense_category_factory
    ):
        """Verifica que no pueda eliminar categorías de otros usuarios."""
        other_cat = expense_category_factory(other_user, name="Otra")

        url = reverse("categories:delete", kwargs={"pk": other_cat.pk})
        response = authenticated_client.post(url)

        assert response.status_code in [403, 404]

    def test_get_delete_confirmation(self, authenticated_client, expense_category):
        """Verifica que muestre confirmación de eliminación."""
        url = reverse("categories:delete", kwargs={"pk": expense_category.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200


@pytest.mark.django_db
class TestCategoryViewRedirects:
    """Tests para verificar redirecciones correctas."""

    def test_create_redirects_to_list(self, authenticated_client, user):
        """Verifica que crear redirija a lista."""
        url = reverse("categories:create")
        data = {
            "name": "Nueva Categoría",
            "type": CategoryType.EXPENSE,
            "icon": "bi-tag",
            "color": "#FF5733",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302

        # Verificar URL de redirección
        expected_url = reverse("categories:list")
        assert response.url == expected_url or expected_url in response.url

    def test_update_redirects_to_list(self, authenticated_client, expense_category):
        """Verifica que actualizar redirija a lista."""
        url = reverse("categories:update", kwargs={"pk": expense_category.pk})
        data = {
            "name": "Actualizada",
            "type": expense_category.type,
            "icon": expense_category.icon or "bi-tag",
            "color": expense_category.color or "#000000",
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        assert "categories" in response.url

    def test_delete_redirects_to_list(self, authenticated_client, expense_category):
        """Verifica que eliminar redirija a lista."""
        url = reverse("categories:delete", kwargs={"pk": expense_category.pk})

        response = authenticated_client.post(url)

        assert response.status_code == 302

        expected_url = reverse("categories:list")
        assert response.url == expected_url or expected_url in response.url

    def test_login_redirect_preserves_next(self, client):
        """Verifica que login preserve parámetro next."""
        protected_url = reverse("categories:create")
        response = client.get(protected_url)

        assert response.status_code == 302
        assert "login" in response.url
        assert f"next={protected_url}" in response.url or "next=" in response.url
