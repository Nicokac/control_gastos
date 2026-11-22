"""Tests para los endpoints de categorías de la API v1."""

from decimal import Decimal

from django.utils import timezone

import pytest

from apps.categories.models import Category, CategoryOverride
from apps.core.constants import CategoryType


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.mark.django_db
class TestCategoryListEndpoint:
    url = "/api/v1/categories/"

    def test_requiere_autenticacion(self, client):
        assert client.get(self.url).status_code == 401

    def test_lista_categorias_propias_y_sistema(
        self, client, user, expense_category, system_expense_group
    ):
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        assert response.status_code == 200
        ids = [c["id"] for c in response.json()["results"]]
        assert expense_category.pk in ids
        assert system_expense_group.pk in ids

    def test_no_muestra_categorias_de_otro_usuario(
        self, client, user, other_user, expense_category_factory
    ):
        other_cat = expense_category_factory(other_user, name="Ajena")
        headers = auth_header(client, user)
        response = client.get(self.url, **headers)
        ids = [c["id"] for c in response.json()["results"]]
        assert other_cat.pk not in ids

    def test_filtro_por_tipo(self, client, user, expense_category, income_category):
        headers = auth_header(client, user)
        response = client.get(self.url + f"?type={CategoryType.EXPENSE}", **headers)
        types = [c["type"] for c in response.json()["results"]]
        assert all(t == CategoryType.EXPENSE for t in types)


@pytest.mark.django_db
class TestCategoryCreateEndpoint:
    url = "/api/v1/categories/"

    def test_crear_subcategoria(self, client, user, system_expense_group):
        headers = auth_header(client, user)
        data = {
            "name": "Nueva sub",
            "type": CategoryType.EXPENSE,
            "parent": system_expense_group.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        assert Category.objects.filter(name="Nueva sub", user=user).exists()

    def test_no_puede_crear_categoria_sistema(self, client, user, system_expense_group):
        headers = auth_header(client, user)
        data = {
            "name": "Intento sistema",
            "type": CategoryType.EXPENSE,
            "is_system": True,
            "icon": "bi-tag",
            "color": "#dc3545",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        # is_system se ignora — siempre queda False
        assert response.status_code == 201
        cat = Category.objects.get(name="Intento sistema", user=user)
        assert cat.is_system is False

    def test_nuevo_grupo_de_gastos_recibe_subcategoria_general(self, client, user):
        """Un grupo de gastos nuevo debe quedar utilizable de inmediato (D-011)."""
        headers = auth_header(client, user)
        data = {
            "name": "Supermercado",
            "type": CategoryType.EXPENSE,
            "icon": "bi-cart",
            "color": "#dc3545",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201

        group = Category.objects.get(name="Supermercado", user=user, parent__isnull=True)
        subcategory = Category.objects.get(parent=group)
        assert subcategory.name == "General"
        assert subcategory.type == CategoryType.EXPENSE
        assert subcategory in Category.get_expense_categories(user)

    def test_nueva_subcategoria_no_dispara_autocompletado(self, client, user, system_expense_group):
        headers = auth_header(client, user)
        data = {
            "name": "Sub manual",
            "type": CategoryType.EXPENSE,
            "parent": system_expense_group.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201

        subcategory = Category.objects.get(name="Sub manual", user=user)
        assert Category.objects.filter(parent=subcategory).count() == 0

    def test_nuevo_grupo_de_ingresos_no_recibe_subcategoria_automatica(self, client, user):
        """Los ingresos no tienen la restricción de D-011; no deben recibir
        subcategoría automática."""
        headers = auth_header(client, user)
        data = {
            "name": "Freelance",
            "type": CategoryType.INCOME,
            "icon": "bi-cash",
            "color": "#28a745",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201

        group = Category.objects.get(name="Freelance", user=user, parent__isnull=True)
        assert Category.objects.filter(parent=group).count() == 0


@pytest.mark.django_db
class TestCategoryValidations:
    url = "/api/v1/categories/"

    def test_tipo_distinto_al_grupo_padre_rechazado(
        self, client, user, system_expense_group, system_income_group
    ):
        headers = auth_header(client, user)
        data = {
            "name": "Sub tipo incorrecto",
            "type": CategoryType.INCOME,
            "parent": system_expense_group.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400

    def test_anidar_mas_de_dos_niveles_rechazado(self, client, user, expense_category):
        headers = auth_header(client, user)
        data = {
            "name": "Sub de sub",
            "type": CategoryType.EXPENSE,
            "parent": expense_category.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400

    def test_nombre_duplicado_rechazado(self, client, user, expense_category, system_expense_group):
        headers = auth_header(client, user)
        data = {
            "name": expense_category.name,
            "type": CategoryType.EXPENSE,
            "parent": system_expense_group.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400


@pytest.mark.django_db
class TestCategoryDeleteEndpoint:
    def test_eliminar_categoria_propia(self, client, user, expense_category):
        headers = auth_header(client, user)
        url = f"/api/v1/categories/{expense_category.pk}/"
        response = client.delete(url, **headers)
        assert response.status_code == 204
        assert not Category.objects.filter(pk=expense_category.pk).exists()

    def test_no_puede_eliminar_categoria_sistema(self, client, user, system_expense_group):
        headers = auth_header(client, user)
        url = f"/api/v1/categories/{system_expense_group.pk}/"
        response = client.delete(url, **headers)
        assert response.status_code in [403, 404]


@pytest.mark.django_db
class TestCategoryHideEndpoint:
    """DT-086 fase 1: ocultar una categoría de sistema por usuario."""

    def test_ocultar_categoria_de_sistema(self, client, user, system_expense_group):
        headers = auth_header(client, user)
        url = f"/api/v1/categories/{system_expense_group.pk}/hide/"
        response = client.post(url, **headers)
        assert response.status_code == 204
        assert CategoryOverride.objects.filter(
            user=user, category=system_expense_group, is_hidden=True
        ).exists()

    def test_no_puede_ocultar_categoria_propia(self, client, user, expense_category):
        headers = auth_header(client, user)
        url = f"/api/v1/categories/{expense_category.pk}/hide/"
        response = client.post(url, **headers)
        assert response.status_code == 403

    def test_ocultar_no_afecta_a_otro_usuario(self, client, user, other_user, system_expense_group):
        headers = auth_header(client, user)
        client.post(f"/api/v1/categories/{system_expense_group.pk}/hide/", **headers)

        token_response = client.post(
            "/api/v1/auth/token/",
            {"username": other_user.email, "password": "otherpass123"},  # pragma: allowlist secret
            content_type="application/json",
        )
        other_headers = {"HTTP_AUTHORIZATION": f"Bearer {token_response.json()['access']}"}
        response = client.get("/api/v1/categories/", **other_headers)
        ids = [c["id"] for c in response.json()["results"]]
        assert system_expense_group.pk in ids

    def test_categoria_oculta_no_aparece_al_listar_para_el_usuario(
        self, client, user, system_expense_group
    ):
        headers = auth_header(client, user)
        client.post(f"/api/v1/categories/{system_expense_group.pk}/hide/", **headers)

        response = client.get("/api/v1/categories/", **headers)
        hidden = next(c for c in response.json()["results"] if c["id"] == system_expense_group.pk)
        assert hidden["is_hidden"] is True

    def test_unhide_revierte_el_ocultamiento(self, client, user, system_expense_group):
        headers = auth_header(client, user)
        client.post(f"/api/v1/categories/{system_expense_group.pk}/hide/", **headers)

        response = client.post(f"/api/v1/categories/{system_expense_group.pk}/unhide/", **headers)
        assert response.status_code == 204
        assert not CategoryOverride.objects.filter(
            user=user, category=system_expense_group, is_hidden=True
        ).exists()


@pytest.mark.django_db
class TestMonthlyAlertThresholdEndpoint:
    """DT-088: umbral de alerta mensual vía API."""

    url = "/api/v1/categories/"

    def test_crear_subcategoria_con_umbral(self, client, user, system_expense_group):
        headers = auth_header(client, user)
        data = {
            "name": "Ropa",
            "type": CategoryType.EXPENSE,
            "parent": system_expense_group.pk,
            "icon": "bi-tag",
            "color": "#dc3545",
            "monthly_alert_threshold": "20000",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 201
        cat = Category.objects.get(name="Ropa", user=user)
        assert cat.monthly_alert_threshold == 20000

    def test_no_puede_asignar_umbral_a_un_grupo(self, client, user):
        headers = auth_header(client, user)
        data = {
            "name": "Grupo con umbral",
            "type": CategoryType.EXPENSE,
            "icon": "bi-tag",
            "color": "#dc3545",
            "monthly_alert_threshold": "20000",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400

    def test_no_puede_asignar_umbral_a_categoria_de_ingreso(
        self, client, user, system_income_group
    ):
        headers = auth_header(client, user)
        data = {
            "name": "Ingreso con umbral",
            "type": CategoryType.INCOME,
            "parent": system_income_group.pk,
            "icon": "bi-tag",
            "color": "#28a745",
            "monthly_alert_threshold": "20000",
        }
        response = client.post(self.url, data, content_type="application/json", **headers)
        assert response.status_code == 400

    def test_is_over_alert_threshold_true_al_superarlo(
        self, client, user, expense_category, expense_factory
    ):
        expense_category.monthly_alert_threshold = Decimal("1000")
        expense_category.save()
        expense_factory(user, expense_category, amount=Decimal("1500"))

        headers = auth_header(client, user)
        response = client.get("/api/v1/categories/", **headers)
        item = next(c for c in response.json()["results"] if c["id"] == expense_category.pk)
        assert item["is_over_alert_threshold"] is True
        assert Decimal(item["current_month_spent"]) == Decimal("1500.00")


@pytest.mark.django_db
class TestCategoryUpdateEndpoint:
    """Edición desde la app mobile: manda el formulario completo por PATCH."""

    def payload(self, category, **extra):
        return {
            "name": category.name,
            "type": category.type,
            "color": "#dc3545",
            "icon": "bi-tag",
            "parent": category.parent_id,
            **extra,
        }

    def test_define_el_umbral_de_una_subcategoria_propia(self, client, user, expense_category):
        response = client.patch(
            f"/api/v1/categories/{expense_category.pk}/",
            self.payload(expense_category, monthly_alert_threshold=20000.0),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 200
        expense_category.refresh_from_db()
        assert expense_category.monthly_alert_threshold == Decimal("20000")
        assert expense_category.color == "#dc3545"

    def test_umbral_null_lo_borra(self, client, user, expense_category):
        expense_category.monthly_alert_threshold = Decimal("1000")
        expense_category.save()

        response = client.patch(
            f"/api/v1/categories/{expense_category.pk}/",
            self.payload(expense_category, monthly_alert_threshold=None),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 200
        expense_category.refresh_from_db()
        assert expense_category.monthly_alert_threshold is None

    def test_conservar_el_mismo_nombre_no_es_duplicado(self, client, user, expense_category):
        response = client.patch(
            f"/api/v1/categories/{expense_category.pk}/",
            self.payload(expense_category),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 200

    def test_no_puede_editar_categoria_sistema(self, client, user, system_expense_group):
        response = client.patch(
            f"/api/v1/categories/{system_expense_group.pk}/",
            {"name": "Otro", "type": CategoryType.EXPENSE},
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code == 403
        system_expense_group.refresh_from_db()
        assert system_expense_group.name != "Otro"

    def test_no_puede_editar_categoria_de_otro_usuario(
        self, client, user, other_user, expense_category_factory
    ):
        ajena = expense_category_factory(user=other_user)

        response = client.patch(
            f"/api/v1/categories/{ajena.pk}/",
            self.payload(ajena, monthly_alert_threshold=5000.0),
            content_type="application/json",
            **auth_header(client, user),
        )

        assert response.status_code in [403, 404]
        ajena.refresh_from_db()
        assert ajena.monthly_alert_threshold is None


@pytest.mark.django_db
class TestSystemCategoryLimitEndpoint:
    """DT-120: límite mensual propio en subcategorías del sistema."""

    @pytest.fixture
    def transporte(self, expense_category_factory):
        return expense_category_factory(user=None, name="Transporte", is_system=True)

    def _post(self, client, headers, category, value):
        return client.post(
            f"/api/v1/categories/{category.pk}/limit/",
            {"monthly_alert_threshold": value},
            content_type="application/json",
            **headers,
        )

    def test_requiere_autenticacion(self, client, transporte):
        assert client.post(f"/api/v1/categories/{transporte.pk}/limit/").status_code == 401

    def test_define_el_limite_y_lo_devuelve(self, client, user, transporte):
        response = self._post(client, auth_header(client, user), transporte, "5000")

        assert response.status_code == 200
        assert Decimal(response.json()["monthly_alert_threshold"]) == Decimal("5000")
        assert transporte.alert_threshold_for(user) == Decimal("5000")
        transporte.refresh_from_db()
        assert transporte.monthly_alert_threshold is None

    def test_null_quita_el_limite(self, client, user, transporte):
        CategoryOverride.objects.create(
            user=user, category=transporte, monthly_alert_threshold=Decimal("5000")
        )

        response = self._post(client, auth_header(client, user), transporte, None)

        assert response.status_code == 200
        assert response.json()["monthly_alert_threshold"] is None
        assert transporte.alert_threshold_for(user) is None

    def test_cero_es_un_limite_valido(self, client, user, transporte):
        self._post(client, auth_header(client, user), transporte, 0)

        assert transporte.alert_threshold_for(user) == Decimal("0")

    def test_negativo_es_invalido(self, client, user, transporte):
        response = self._post(client, auth_header(client, user), transporte, "-1")

        assert response.status_code == 400
        assert "monthly_alert_threshold" in response.json()

    def test_rechaza_grupos_e_ingresos(
        self, client, user, system_expense_group, system_income_category
    ):
        headers = auth_header(client, user)

        for category in (system_expense_group, system_income_category):
            assert self._post(client, headers, category, "100").status_code == 400
        assert not CategoryOverride.objects.exists()

    def test_rechaza_categorias_propias(self, client, user, expense_category_factory):
        own = expense_category_factory(user=user)

        response = self._post(client, auth_header(client, user), own, "100")

        assert response.status_code == 403

    def test_el_listado_muestra_el_limite_de_cada_usuario(
        self, client, user, other_user, transporte, expense_factory
    ):
        CategoryOverride.objects.create(
            user=user, category=transporte, monthly_alert_threshold=Decimal("1000")
        )
        expense_factory(user, transporte, amount=Decimal("1500"), date=timezone.localdate())
        headers = auth_header(client, user)

        data = {c["id"]: c for c in client.get("/api/v1/categories/", **headers).json()["results"]}

        assert Decimal(data[transporte.pk]["monthly_alert_threshold"]) == Decimal("1000")
        assert Decimal(data[transporte.pk]["current_month_spent"]) == Decimal("1500")
        assert data[transporte.pk]["is_over_alert_threshold"] is True

        other_user.set_password("testpass123")  # pragma: allowlist secret
        other_user.save()
        other = auth_header(client, other_user)
        data = {c["id"]: c for c in client.get("/api/v1/categories/", **other).json()["results"]}
        assert data[transporte.pk]["monthly_alert_threshold"] is None
        assert data[transporte.pk]["is_over_alert_threshold"] is False

    def test_unhide_conserva_el_limite(self, client, user, transporte):
        CategoryOverride.objects.create(
            user=user, category=transporte, is_hidden=True, monthly_alert_threshold=Decimal("100")
        )
        headers = auth_header(client, user)

        client.post(f"/api/v1/categories/{transporte.pk}/unhide/", **headers)

        override = CategoryOverride.objects.get(user=user, category=transporte)
        assert not override.is_hidden
        assert override.monthly_alert_threshold == Decimal("100")

    def test_las_preferencias_se_leen_una_vez(
        self, client, user, expense_category_factory, django_assert_max_num_queries
    ):
        for i in range(10):
            category = expense_category_factory(user=None, name=f"Sistema {i}", is_system=True)
            CategoryOverride.objects.create(user=user, category=category, is_hidden=True)
        headers = auth_header(client, user)

        with django_assert_max_num_queries(6):
            response = client.get("/api/v1/categories/", **headers)

        assert sum(c["is_hidden"] for c in response.json()["results"]) == 10
