"""
Tests para las vistas de Category.
"""

import json

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
            "color": "#dc3545",
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
        assert "No pudimos guardar la categoría." in response.content.decode()

    def test_category_assigned_to_current_user(self, authenticated_client, user):
        """Verifica que la categoría se asigne al usuario actual."""
        url = reverse("categories:create")
        data = {
            "name": "Mi Categoría",
            "type": CategoryType.EXPENSE,
            "icon": "bi-cart",
            "color": "#6c757d",
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
            "color": expense_category.color or "#6c757d",
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

        from apps.categories.models import Category

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

    def test_delete_group_with_children_shows_warning(
        self, authenticated_client, user, expense_category_factory
    ):
        """GET a un grupo con subcategorías muestra advertencia, no formulario de confirmación."""
        group = Category.objects.create(
            name="Grupo con hijos",
            type=CategoryType.EXPENSE,
            user=user,
            parent=None,
            icon="bi-tag",
            color="#dc3545",
        )
        expense_category_factory(user=user, parent=group, name="SubA")
        url = reverse("categories:delete", kwargs={"pk": group.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "SubA" in content
        assert "Sí, eliminar" not in content

    def test_delete_group_with_children_post_redirects_with_error(
        self, authenticated_client, user, expense_category_factory
    ):
        """POST a un grupo con subcategorías no elimina y redirige con mensaje de error."""
        group = Category.objects.create(
            name="Grupo protegido",
            type=CategoryType.EXPENSE,
            user=user,
            parent=None,
            icon="bi-tag",
            color="#dc3545",
        )
        expense_category_factory(user=user, parent=group, name="SubB")
        url = reverse("categories:delete", kwargs={"pk": group.pk})
        response = authenticated_client.post(url, follow=True)

        assert Category.objects.filter(pk=group.pk).exists()
        msgs = [m.message for m in response.context["messages"]]
        assert any("subcategoría" in m.lower() for m in msgs)

    def test_delete_group_without_children_succeeds(self, authenticated_client, user):
        """Un grupo vacío se puede eliminar sin problemas."""
        group = Category.objects.create(
            name="Grupo vacío",
            type=CategoryType.EXPENSE,
            user=user,
            parent=None,
            icon="bi-tag",
            color="#dc3545",
        )
        url = reverse("categories:delete", kwargs={"pk": group.pk})
        authenticated_client.post(url)
        assert not Category.objects.filter(pk=group.pk).exists()


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
            "color": "#dc3545",
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
            "color": expense_category.color or "#6c757d",
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


@pytest.mark.django_db
class TestCategoryToastMessages:
    """Tests de mensajes toast para operaciones CRUD de categorías."""

    def test_create_category_success_adds_toast(self, authenticated_client, user):
        url = reverse("categories:create")
        data = {
            "name": "Categoría Toast",
            "type": CategoryType.EXPENSE,
            "icon": "bi-tag",
            "color": "#dc3545",
        }

        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        assert Category.objects.filter(name="Categoría Toast", user=user).exists()
        msgs = [m.message for m in response.context["messages"]]
        assert any("Categoría creada" in m for m in msgs)

    def test_update_category_success_adds_toast(self, authenticated_client, expense_category):
        url = reverse("categories:update", kwargs={"pk": expense_category.pk})
        data = {
            "name": "Categoría Editada Toast",
            "type": expense_category.type,
            "icon": expense_category.icon or "bi-tag",
            "color": expense_category.color or "#6c757d",
        }

        response = authenticated_client.post(url, data, follow=True)

        assert response.status_code == 200
        expense_category.refresh_from_db()
        assert expense_category.name == "Categoría Editada Toast"
        msgs = [m.message for m in response.context["messages"]]
        assert any("Categoría actualizada" in m for m in msgs)

    def test_delete_category_success_adds_toast(self, authenticated_client, expense_category):
        cat_name = expense_category.name
        cat_pk = expense_category.pk
        url = reverse("categories:delete", kwargs={"pk": cat_pk})

        response = authenticated_client.post(url, follow=True)

        assert response.status_code == 200
        assert not Category.objects.filter(pk=cat_pk).exists()
        msgs = [m.message for m in response.context["messages"]]
        assert any(cat_name in m for m in msgs)


@pytest.mark.django_db
class TestCategoryMoveSubcategory:
    """Tests para mover subcategorías entre grupos (Fase 5)."""

    def test_move_subcategory_to_another_group(self, authenticated_client, user, expense_category):
        """Editar una subcategoría cambiando su grupo padre."""
        from apps.categories.models import Category
        from apps.core.constants import CategoryType

        new_group = Category.objects.create(
            name="Nuevo Grupo", type=CategoryType.EXPENSE, user=user, parent=None, is_system=False
        )
        url = reverse("categories:update", kwargs={"pk": expense_category.pk})
        data = {
            "name": expense_category.name,
            "type": expense_category.type,
            "parent": new_group.pk,
            "icon": expense_category.icon or "",
            "color": expense_category.color or "#6c757d",
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == 302
        expense_category.refresh_from_db()
        assert expense_category.parent == new_group

    def test_update_view_shows_parent_field_for_subcategory(
        self, authenticated_client, expense_category
    ):
        """El formulario de edición muestra el campo parent para subcategorías."""
        url = reverse("categories:update", kwargs={"pk": expense_category.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["is_subcategory"] is True
        assert "parent" in response.context["form"].fields

    def test_update_view_does_not_show_parent_for_group(
        self, authenticated_client, user, system_expense_group
    ):
        """El formulario de edición de un grupo no muestra campo parent (es grupo)."""
        # Solo podemos editar grupos del usuario, así que creamos uno
        from apps.categories.models import Category
        from apps.core.constants import CategoryType

        user_group = Category.objects.create(
            name="Mi grupo edit", type=CategoryType.EXPENSE, user=user, parent=None, is_system=False
        )
        url = reverse("categories:update", kwargs={"pk": user_group.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["is_subcategory"] is False

    def test_preset_parent_on_create_via_querystring(
        self, authenticated_client, user, system_expense_group
    ):
        """?parent=<pk> pre-selecciona el grupo en el formulario de creación."""
        url = reverse("categories:create") + f"?parent={system_expense_group.pk}"
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.context["preset_parent"] == system_expense_group


@pytest.mark.django_db
class TestCategoryReorderView:
    """Tests para el endpoint de reordenamiento de grupos."""

    def test_login_required(self, client):
        url = reverse("categories:reorder")
        response = client.post(url, data=json.dumps({"ids": []}), content_type="application/json")
        assert response.status_code == 302
        assert "login" in response.url

    def test_reorder_updates_order_field(self, authenticated_client, user):
        g1 = Category.objects.create(
            name="Grupo A", type=CategoryType.EXPENSE, user=user, parent=None, is_system=False
        )
        g2 = Category.objects.create(
            name="Grupo B", type=CategoryType.EXPENSE, user=user, parent=None, is_system=False
        )
        url = reverse("categories:reorder")
        response = authenticated_client.post(
            url,
            data=json.dumps({"ids": [g2.pk, g1.pk]}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json()["ok"] is True
        g1.refresh_from_db()
        g2.refresh_from_db()
        assert g2.order < g1.order

    def test_cannot_reorder_other_user_groups(self, authenticated_client, other_user):
        other_group = Category.objects.create(
            name="Grupo Otro",
            type=CategoryType.EXPENSE,
            user=other_user,
            parent=None,
            is_system=False,
        )
        url = reverse("categories:reorder")
        response = authenticated_client.post(
            url,
            data=json.dumps({"ids": [other_group.pk]}),
            content_type="application/json",
        )

        assert response.status_code == 200
        other_group.refresh_from_db()
        assert other_group.order == 0

    def test_invalid_body_returns_400(self, authenticated_client):
        url = reverse("categories:reorder")
        response = authenticated_client.post(
            url, data="no-es-json", content_type="application/json"
        )
        assert response.status_code == 400
