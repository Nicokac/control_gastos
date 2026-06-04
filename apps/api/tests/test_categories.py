"""Tests para los endpoints de categorías de la API v1."""

import pytest

from apps.categories.models import Category
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
