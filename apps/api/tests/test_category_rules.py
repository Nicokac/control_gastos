"""Tests del endpoint de reglas de categorización de la API v1 (pantalla Reglas en mobile)."""

import pytest

from apps.categories.models import CategoryOverride, CategoryRule

URL = "/api/v1/category-rules/"


def auth_header(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.email, "password": "testpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['access']}"}


@pytest.fixture
def headers(client, user):
    return auth_header(client, user)


@pytest.mark.django_db
class TestCategoryRuleList:
    def test_requiere_autenticacion(self, client):
        assert client.get(URL).status_code == 401

    def test_lista_solo_las_reglas_propias_con_nombres(
        self, client, headers, user, other_user, expense_category, expense_category_factory
    ):
        CategoryRule.objects.create(user=user, pattern="super", category=expense_category)
        ajena = expense_category_factory(user=other_user, name="Ajena")
        CategoryRule.objects.create(user=other_user, pattern="netflix", category=ajena)

        results = client.get(URL, **headers).json()["results"]

        assert results == [
            {
                "id": results[0]["id"],
                "pattern": "super",
                "category": expense_category.pk,
                "category_name": "Alimentación",
                "group_name": "Otros gastos",
            }
        ]

    def test_ordena_por_texto_sin_consultas_por_regla(
        self, client, headers, user, expense_category, django_assert_max_num_queries
    ):
        for pattern in ("zeta", "alfa", "medio"):
            CategoryRule.objects.create(user=user, pattern=pattern, category=expense_category)

        with django_assert_max_num_queries(6):
            results = client.get(URL, **headers).json()["results"]

        assert [r["pattern"] for r in results] == ["alfa", "medio", "zeta"]


@pytest.mark.django_db
class TestCategoryRuleCreate:
    def test_crea_la_regla_normalizando_el_texto(self, client, headers, user, expense_category):
        response = client.post(
            URL,
            {"pattern": "  Farmacia   CENTRAL! ", "category": expense_category.pk},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 201
        assert response.json()["pattern"] == "farmacia central"
        assert CategoryRule.objects.get(user=user).pattern == "farmacia central"

    def test_texto_repetido_da_error_en_el_campo(self, client, headers, user, expense_category):
        CategoryRule.objects.create(user=user, pattern="super", category=expense_category)

        response = client.post(
            URL,
            {"pattern": "Súper", "category": expense_category.pk},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 400
        assert response.json()["pattern"] == ["Ya tenés una regla con ese texto."]

    def test_el_mismo_texto_de_otro_usuario_no_cuenta_como_repetido(
        self, client, headers, other_user, expense_category, expense_category_factory
    ):
        ajena = expense_category_factory(user=other_user, name="Ajena")
        CategoryRule.objects.create(user=other_user, pattern="super", category=ajena)

        response = client.post(
            URL,
            {"pattern": "super", "category": expense_category.pk},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 201

    def test_texto_sin_palabras_da_error(self, client, headers, expense_category):
        response = client.post(
            URL,
            {"pattern": "¡¡!!", "category": expense_category.pk},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 400
        assert response.json()["pattern"] == ["Escribí al menos una palabra."]

    @pytest.mark.parametrize("kind", ["ajena", "ingreso", "oculta"])
    def test_categoria_no_disponible_da_error(
        self,
        client,
        headers,
        user,
        other_user,
        kind,
        expense_category_factory,
        income_category,
        system_expense_category,
    ):
        if kind == "ajena":
            category = expense_category_factory(user=other_user, name="Ajena")
        elif kind == "ingreso":
            category = income_category
        else:
            category = system_expense_category
            CategoryOverride.objects.create(user=user, category=category, is_hidden=True)

        response = client.post(
            URL,
            {"pattern": "algo", "category": category.pk},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 400
        assert response.json()["category"] == ["Elegí una subcategoría de gasto."]
        assert not CategoryRule.objects.exists()


@pytest.mark.django_db
class TestCategoryRuleUpdateDelete:
    def test_edita_texto_y_categoria(
        self, client, headers, user, expense_category, expense_category_factory
    ):
        rule = CategoryRule.objects.create(user=user, pattern="super", category=expense_category)
        otra = expense_category_factory(user=user, name="Verdulería")

        response = client.put(
            f"{URL}{rule.pk}/",
            {"pattern": "verdu", "category": otra.pk},
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 200
        rule.refresh_from_db()
        assert (rule.pattern, rule.category) == ("verdu", otra)

    def test_guardar_sin_cambiar_el_texto_no_es_repetido(
        self, client, headers, user, expense_category
    ):
        rule = CategoryRule.objects.create(user=user, pattern="super", category=expense_category)

        response = client.patch(
            f"{URL}{rule.pk}/", {"pattern": "super"}, content_type="application/json", **headers
        )

        assert response.status_code == 200

    def test_borra_la_regla(self, client, headers, user, expense_category):
        rule = CategoryRule.objects.create(user=user, pattern="super", category=expense_category)

        assert client.delete(f"{URL}{rule.pk}/", **headers).status_code == 204
        assert not CategoryRule.objects.exists()

    @pytest.mark.parametrize("method", ["get", "patch", "delete"])
    def test_la_regla_de_otro_usuario_da_404(
        self, client, headers, other_user, expense_category_factory, method
    ):
        ajena = expense_category_factory(user=other_user, name="Ajena")
        rule = CategoryRule.objects.create(user=other_user, pattern="netflix", category=ajena)

        response = getattr(client, method)(
            f"{URL}{rule.pk}/",
            {"pattern": "x"} if method == "patch" else None,
            content_type="application/json",
            **headers,
        )

        assert response.status_code == 404
        assert CategoryRule.objects.filter(pk=rule.pk, pattern="netflix").exists()
