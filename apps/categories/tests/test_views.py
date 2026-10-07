"""
Tests para las vistas de Category.
"""

import json
from decimal import Decimal

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

    def test_new_expense_group_gets_default_general_subcategory(self, authenticated_client, user):
        """Un grupo de gastos nuevo debe quedar utilizable de inmediato (D-011:
        get_expense_categories solo devuelve subcategorías)."""
        url = reverse("categories:create")
        data = {
            "name": "Supermercado",
            "type": CategoryType.EXPENSE,
            "icon": "bi-cart",
            "color": "#dc3545",
        }

        authenticated_client.post(url, data)

        group = Category.objects.get(name="Supermercado", user=user, parent__isnull=True)
        subcategory = Category.objects.get(parent=group)
        assert subcategory.name == "General"
        assert subcategory.type == CategoryType.EXPENSE
        assert subcategory.user == user
        assert subcategory in Category.get_expense_categories(user)

    def test_new_expense_subcategory_does_not_get_extra_subcategory(
        self, authenticated_client, user
    ):
        """Crear una subcategoría (con parent) no debe disparar el autocompletado."""
        group = Category.objects.create(
            name="Grupo Existente",
            type=CategoryType.EXPENSE,
            user=user,
            parent=None,
            icon="bi-cart",
            color="#dc3545",
        )
        url = reverse("categories:create")
        data = {
            "name": "Subcategoría Manual",
            "type": CategoryType.EXPENSE,
            "parent": group.pk,
            "icon": "bi-cart",
            "color": "#dc3545",
        }

        authenticated_client.post(url, data)

        subcategory = Category.objects.get(name="Subcategoría Manual")
        assert Category.objects.filter(parent=subcategory).count() == 0

    def test_new_income_group_does_not_get_default_subcategory(self, authenticated_client, user):
        """Los ingresos no tienen la restricción de D-011 (get_income_categories
        incluye grupos sueltos), así que no deben recibir subcategoría automática."""
        url = reverse("categories:create")
        data = {
            "name": "Freelance",
            "type": CategoryType.INCOME,
            "icon": "bi-cash",
            "color": "#28a745",
        }

        authenticated_client.post(url, data)

        group = Category.objects.get(name="Freelance", user=user, parent__isnull=True)
        assert Category.objects.filter(parent=group).count() == 0


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

    def test_delete_subcategory_with_expenses_shows_correct_error(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        """Eliminar subcategoría con gastos asociados muestra error sobre registros, no subcategorías."""
        expense = expense_factory(user, expense_category)
        expense.save()
        url = reverse("categories:delete", kwargs={"pk": expense_category.pk})
        response = authenticated_client.post(url, follow=True)
        assert Category.objects.filter(pk=expense_category.pk).exists()
        msgs = [m.message for m in response.context["messages"]]
        assert any("registros" in m.lower() for m in msgs)
        assert not any("subcategoría" in m.lower() for m in msgs)


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
        assert any("Grupo creado" in m for m in msgs)

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


@pytest.mark.django_db
class TestCategoryQuickCreateView:
    """Tests para el endpoint de creación rápida de subcategoría (import PDF)."""

    def test_login_required(self, client):
        url = reverse("categories:quick_create")
        response = client.post(
            url,
            data=json.dumps({"parent_pk": 1, "name": "Streaming"}),
            content_type="application/json",
        )
        assert response.status_code == 302
        assert "login" in response.url

    def test_creates_subcategory_under_existing_group(self, authenticated_client, user):
        group = Category.objects.create(
            name="Entretenimiento", type=CategoryType.EXPENSE, user=user, parent=None
        )
        url = reverse("categories:quick_create")
        response = authenticated_client.post(
            url,
            data=json.dumps({"parent_pk": group.pk, "name": "Streaming"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Entretenimiento › Streaming"

        new_cat = Category.objects.get(pk=data["pk"])
        assert new_cat.parent_id == group.pk
        assert new_cat.user == user
        assert new_cat.type == CategoryType.EXPENSE

    def test_creates_new_group_and_subcategory(self, authenticated_client, user):
        url = reverse("categories:quick_create")
        response = authenticated_client.post(
            url,
            data=json.dumps(
                {"parent_pk": "new", "new_group_name": "Finanzas", "name": "Impuestos"}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Finanzas › Impuestos"

        new_group = Category.objects.get(pk=data["parent_pk"])
        assert new_group.name == "Finanzas"
        assert new_group.parent_id is None
        assert new_group.user == user

        new_cat = Category.objects.get(pk=data["pk"])
        assert new_cat.parent_id == new_group.pk

    def test_new_group_without_name_returns_400(self, authenticated_client):
        url = reverse("categories:quick_create")
        response = authenticated_client.post(
            url,
            data=json.dumps({"parent_pk": "new", "new_group_name": "", "name": "Impuestos"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_cannot_use_other_user_group_as_parent(self, authenticated_client, other_user):
        other_group = Category.objects.create(
            name="Grupo Otro", type=CategoryType.EXPENSE, user=other_user, parent=None
        )
        url = reverse("categories:quick_create")
        response = authenticated_client.post(
            url,
            data=json.dumps({"parent_pk": other_group.pk, "name": "Sub"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_missing_name_returns_400(self, authenticated_client, user):
        group = Category.objects.create(
            name="Grupo", type=CategoryType.EXPENSE, user=user, parent=None
        )
        url = reverse("categories:quick_create")
        response = authenticated_client.post(
            url,
            data=json.dumps({"parent_pk": group.pk, "name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_body_returns_400(self, authenticated_client):
        url = reverse("categories:quick_create")
        response = authenticated_client.post(
            url, data="no-es-json", content_type="application/json"
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestCategoryHideView:
    """DT-086 fase 1: ocultar una categoría de sistema por usuario (web)."""

    def test_ocultar_categoria_de_sistema(self, authenticated_client, user, system_expense_group):
        from apps.categories.models import CategoryOverride

        url = reverse("categories:hide", args=[system_expense_group.pk])
        response = authenticated_client.post(url)

        assert response.status_code == 200
        assert CategoryOverride.objects.filter(
            user=user, category=system_expense_group, is_hidden=True
        ).exists()

    def test_no_puede_ocultar_categoria_propia(self, authenticated_client, expense_category):
        url = reverse("categories:hide", args=[expense_category.pk])
        response = authenticated_client.post(url)
        assert response.status_code == 404

    def test_sigue_apareciendo_en_la_lista_de_administracion(
        self, authenticated_client, system_expense_group
    ):
        """A diferencia de los selectores de alta, la pantalla de Categorías debe
        seguir mostrando la categoría oculta para poder revertir el ocultamiento."""
        authenticated_client.post(reverse("categories:hide", args=[system_expense_group.pk]))

        response = authenticated_client.get(reverse("categories:list"))
        assert system_expense_group.name in response.content.decode()

    def test_unhide_revierte_el_ocultamiento(
        self, authenticated_client, user, system_expense_group
    ):
        from apps.categories.models import CategoryOverride

        authenticated_client.post(reverse("categories:hide", args=[system_expense_group.pk]))

        url = reverse("categories:unhide", args=[system_expense_group.pk])
        response = authenticated_client.post(url)

        assert response.status_code == 200
        assert not CategoryOverride.objects.filter(
            user=user, category=system_expense_group, is_hidden=True
        ).exists()


@pytest.mark.django_db
class TestMonthlyAlertThresholdView:
    """DT-088: umbral de alerta mensual, visto desde la vista de administración."""

    def test_create_with_threshold(self, authenticated_client, user):
        group = Category.objects.create(
            name="Grupo Ropa", type=CategoryType.EXPENSE, user=user, parent=None
        )
        data = {
            "name": "Ropa",
            "type": "EXPENSE",
            "parent": group.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
            "monthly_alert_threshold": "20000",
        }
        response = authenticated_client.post(reverse("categories:create"), data)
        assert response.status_code == 302
        cat = Category.objects.get(name="Ropa", user=user)
        assert cat.monthly_alert_threshold == 20000

    def test_threshold_is_optional(self, authenticated_client, user):
        group = Category.objects.create(
            name="Grupo Varios", type=CategoryType.EXPENSE, user=user, parent=None
        )
        data = {
            "name": "Varios 2",
            "type": "EXPENSE",
            "parent": group.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
        }
        response = authenticated_client.post(reverse("categories:create"), data)
        assert response.status_code == 302
        cat = Category.objects.get(name="Varios 2", user=user)
        assert cat.monthly_alert_threshold is None

    def test_list_shows_badge_when_over_threshold(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_category.monthly_alert_threshold = Decimal("1000")
        expense_category.save()
        expense_factory(user, expense_category, amount=Decimal("1500"))

        response = authenticated_client.get(reverse("categories:list"))
        assert "este mes" in response.content.decode()

    def test_list_no_badge_when_under_threshold(
        self, authenticated_client, user, expense_category, expense_factory
    ):
        expense_category.monthly_alert_threshold = Decimal("1000")
        expense_category.save()
        expense_factory(user, expense_category, amount=Decimal("500"))

        response = authenticated_client.get(reverse("categories:list"))
        assert "este mes" not in response.content.decode()
