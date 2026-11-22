"""Límite mensual propio en subcategorías del sistema (DT-120)."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

import pytest

from apps.categories.models import CategoryOverride


@pytest.fixture
def transporte(expense_category_factory):
    return expense_category_factory(user=None, name="Transporte", is_system=True)


def _limit(user, category, amount):
    return CategoryOverride.objects.create(
        user=user, category=category, monthly_alert_threshold=Decimal(amount)
    )


@pytest.mark.django_db
class TestAlertThresholdFor:
    def test_propia_usa_su_propio_limite(self, user, expense_category_factory):
        own = expense_category_factory(user=user, monthly_alert_threshold=Decimal("100"))

        assert own.alert_threshold_for(user) == Decimal("100")

    def test_sistema_usa_el_limite_del_usuario(self, user, other_user, transporte):
        _limit(user, transporte, "5000")

        assert transporte.alert_threshold_for(user) == Decimal("5000")
        assert transporte.alert_threshold_for(other_user) is None

    def test_supera_el_limite_con_gastos_del_usuario(
        self, user, other_user, transporte, expense_factory
    ):
        _limit(user, transporte, "5000")
        _limit(other_user, transporte, "5000")
        expense_factory(user, transporte, amount=Decimal("5000"), date=timezone.localdate())

        assert transporte.is_over_alert_threshold(user)
        assert not transporte.is_over_alert_threshold(other_user)

    def test_no_se_puede_en_un_grupo(self, user, system_expense_group):
        with pytest.raises(ValidationError):
            _limit(user, system_expense_group, "100")

    def test_no_se_puede_en_ingresos(self, user, system_income_category):
        with pytest.raises(ValidationError):
            _limit(user, system_income_category, "100")


@pytest.mark.django_db
class TestCategoryLimitView:
    def test_requiere_login(self, client, transporte):
        response = client.get(reverse("categories:limit", args=[transporte.pk]))

        assert response.status_code == 302

    def test_muestra_el_formulario(self, authenticated_client, transporte):
        response = authenticated_client.get(reverse("categories:limit", args=[transporte.pk]))

        assert response.status_code == 200
        assert "Límite mensual de Transporte" in response.content.decode()

    def test_guarda_el_limite(self, authenticated_client, user, transporte):
        response = authenticated_client.post(
            reverse("categories:limit", args=[transporte.pk]),
            {"monthly_alert_threshold": "5000"},
            follow=True,
        )

        assert response.redirect_chain[-1][0] == reverse("categories:list")
        assert transporte.alert_threshold_for(user) == Decimal("5000")
        assert "Límite de Transporte actualizado." in [str(m) for m in response.context["messages"]]

    def test_vaciar_quita_el_limite(self, authenticated_client, user, transporte):
        _limit(user, transporte, "5000")

        authenticated_client.post(
            reverse("categories:limit", args=[transporte.pk]), {"monthly_alert_threshold": ""}
        )

        assert transporte.alert_threshold_for(user) is None

    def test_monto_negativo_es_invalido(self, authenticated_client, user, transporte):
        response = authenticated_client.post(
            reverse("categories:limit", args=[transporte.pk]), {"monthly_alert_threshold": "-1"}
        )

        assert response.status_code == 200
        assert response.context["form"].errors
        assert transporte.alert_threshold_for(user) is None

    def test_no_modifica_la_categoria_compartida(self, authenticated_client, transporte):
        authenticated_client.post(
            reverse("categories:limit", args=[transporte.pk]), {"monthly_alert_threshold": "5000"}
        )

        transporte.refresh_from_db()
        assert transporte.monthly_alert_threshold is None

    def test_conserva_si_estaba_oculta(self, authenticated_client, user, transporte):
        CategoryOverride.objects.create(user=user, category=transporte, is_hidden=True)

        authenticated_client.post(
            reverse("categories:limit", args=[transporte.pk]), {"monthly_alert_threshold": "5000"}
        )

        override = CategoryOverride.objects.get(user=user, category=transporte)
        assert override.is_hidden
        assert override.monthly_alert_threshold == Decimal("5000")

    @pytest.mark.parametrize("target", ["group", "income", "own"])
    def test_solo_subcategorias_de_gasto_del_sistema(
        self,
        authenticated_client,
        user,
        target,
        system_expense_group,
        system_income_category,
        expense_category_factory,
    ):
        category = {
            "group": system_expense_group,
            "income": system_income_category,
            "own": expense_category_factory(user=user),
        }[target]

        response = authenticated_client.get(reverse("categories:limit", args=[category.pk]))

        assert response.status_code == 404


@pytest.mark.django_db
class TestCategoryListWithSystemLimit:
    def test_marca_limite_superado_con_el_limite_del_usuario(
        self, authenticated_client, user, transporte, expense_factory
    ):
        _limit(user, transporte, "1000")
        expense_factory(user, transporte, amount=Decimal("1500"), date=timezone.localdate())

        response = authenticated_client.get(reverse("categories:list"))

        subcats = [
            s
            for entry in response.context["expense_tree"]
            for s in entry["subcategories"]
            if s.pk == transporte.pk
        ]
        assert subcats[0].alert_threshold == Decimal("1000")
        assert subcats[0].is_over_threshold
        assert reverse("categories:limit", args=[transporte.pk]) in response.content.decode()

    def test_mostrar_una_oculta_conserva_el_limite(self, authenticated_client, user, transporte):
        CategoryOverride.objects.create(
            user=user, category=transporte, is_hidden=True, monthly_alert_threshold=Decimal("100")
        )

        authenticated_client.post(reverse("categories:unhide", args=[transporte.pk]))

        override = CategoryOverride.objects.get(user=user, category=transporte)
        assert not override.is_hidden
        assert override.monthly_alert_threshold == Decimal("100")
