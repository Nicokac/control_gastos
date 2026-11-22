"""Tests de las observaciones automáticas del último período cerrado (DT-056)."""

from datetime import date
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.recurring.tests.test_detection import months_back
from apps.reports.insights import build_monthly_insights, last_closed_period

TODAY = date(2026, 11, 22)
HISTORY = [(2026, m) for m in range(4, 10)]


@pytest.fixture
def delivery(user, expense_category_factory):
    return expense_category_factory(user=user, name="Delivery")


@pytest.fixture
def super_(user, expense_category_factory):
    return expense_category_factory(user=user, name="Supermercado")


@pytest.fixture
def spend(user, expense_factory):
    def _spend(category, amount, year, month, day=15, owner=None, **kwargs):
        return expense_factory(
            owner or user, category, date=date(year, month, day), amount=Decimal(amount), **kwargs
        )

    return _spend


@pytest.fixture
def earn(user, income_category, income_factory):
    def _earn(amount, year, month, day=15):
        return income_factory(
            user, income_category, amount=Decimal(amount), date=date(year, month, day)
        )

    return _earn


@pytest.fixture
def baseline(spend, delivery, super_):
    """Abril a septiembre: 10.000 en Delivery y 20.000 en Supermercado por mes."""
    for year, month in HISTORY:
        spend(delivery, 10000, year, month)
        spend(super_, 20000, year, month)


def insights(user, today=TODAY):
    return build_monthly_insights(user, today.month, today.year, today)


def texts(result):
    return [item.text for item in result.items]


class TestLastClosedPeriod:
    def test_mes_en_curso_resume_el_anterior(self):
        assert last_closed_period(11, 2026, 1, TODAY) == (10, 2026)

    def test_enero_resume_diciembre_del_anio_anterior(self):
        assert last_closed_period(1, 2027, 1, date(2027, 1, 5)) == (12, 2026)

    def test_periodo_anterior_todavia_abierto_retrocede_uno_mas(self):
        # Con inicio el 25, el período de octubre va del 25/10 al 25/11: todavía no cerró.
        assert last_closed_period(11, 2026, 25, TODAY) == (9, 2026)

    def test_periodo_anterior_ya_cerrado_con_inicio_distinto_de_1(self):
        assert last_closed_period(11, 2026, 10, TODAY) == (10, 2026)

    def test_mes_pasado_seleccionado_se_resume_a_si_mismo(self):
        assert last_closed_period(8, 2026, 1, TODAY) == (8, 2026)

    def test_mes_pasado_todavia_abierto_retrocede(self):
        assert last_closed_period(10, 2026, 25, TODAY) == (9, 2026)


@pytest.mark.django_db
class TestMinimumData:
    def test_sin_historial_suficiente_no_hay_resumen(self, user, spend, delivery):
        for month in (8, 9):
            spend(delivery, 10000, 2026, month)
        spend(delivery, 20000, 2026, 10)

        assert insights(user) is None

    def test_sin_gastos_en_el_periodo_no_hay_resumen(self, user, baseline):
        assert insights(user) is None

    def test_sin_cambios_relevantes_no_hay_resumen(self, user, baseline, spend, delivery, super_):
        spend(delivery, 10000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        assert insights(user) is None

    def test_ignora_los_gastos_de_otro_usuario(
        self, user, other_user, baseline, spend, delivery, super_, expense_category_factory
    ):
        spend(delivery, 10000, 2026, 10)
        spend(super_, 20000, 2026, 10)
        ajena = expense_category_factory(user=other_user, name="Delivery")
        spend(ajena, 90000, 2026, 10, owner=other_user)

        assert insights(user) is None


@pytest.mark.django_db
class TestCategoryRules:
    def test_subcategoria_por_encima_del_promedio(self, user, baseline, spend, delivery, super_):
        spend(delivery, 15000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        result = insights(user)

        assert (result.month, result.year, result.label) == (10, 2026, "Octubre")
        assert texts(result) == [
            "Gastaste 50% más en Delivery que tu promedio de los últimos 6 meses "
            "($ 15.000 contra $ 10.000).",
            "En total gastaste 17% más que tu promedio de los últimos 6 meses "
            "($ 35.000 contra $ 30.000).",
        ]
        assert result.items[0].tone == "warning"

    def test_suba_justo_en_25_por_ciento_cuenta(self, user, baseline, spend, delivery, super_):
        spend(delivery, 12500, 2026, 10)
        spend(super_, 20000, 2026, 10)

        assert [i.kind for i in insights(user).items] == ["category_up"]

    def test_suba_menor_al_25_por_ciento_no_cuenta(self, user, baseline, spend, delivery, super_):
        spend(delivery, 12400, 2026, 10)
        spend(super_, 20000, 2026, 10)

        assert insights(user) is None

    def test_diferencia_chica_frente_al_total_no_cuenta(
        self, user, spend, delivery, super_, expense_category_factory
    ):
        # Delivery se duplica, pero 1.000 es apenas el 1% de lo gastado en el período.
        for year, month in HISTORY:
            spend(delivery, 1000, year, month)
            spend(super_, 100000, year, month)
        spend(delivery, 2000, 2026, 10)
        spend(super_, 100000, 2026, 10)

        assert insights(user) is None

    def test_subcategoria_por_debajo_del_promedio(self, user, baseline, spend, delivery, super_):
        spend(delivery, 5000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        result = insights(user)

        assert result.items[0].kind == "category_down"
        assert result.items[0].tone == "positive"
        assert result.items[0].text == (
            "Gastaste 50% menos en Delivery que tu promedio de los últimos 6 meses "
            "($ 5.000 contra $ 10.000)."
        )

    def test_subcategoria_sin_gastos_en_el_periodo(self, user, baseline, spend, super_):
        spend(super_, 20000, 2026, 10)

        assert texts(insights(user))[0] == (
            "No gastaste en Delivery, cuando tu promedio de los últimos 6 meses es de $ 10.000."
        )

    def test_subcategoria_nueva_no_genera_observacion(
        self, user, baseline, spend, delivery, super_, expense_category_factory
    ):
        nueva = expense_category_factory(user=user, name="Viajes")
        spend(delivery, 10000, 2026, 10)
        spend(super_, 20000, 2026, 10)
        spend(nueva, 2000, 2026, 10)

        assert insights(user) is None

    def test_nombres_repetidos_muestran_el_grupo(self, user, spend, expense_category_factory):
        hogar = Category.objects.create(user=user, name="Hogar", type=CategoryType.EXPENSE)
        auto = Category.objects.create(user=user, name="Auto", type=CategoryType.EXPENSE)
        general_hogar = expense_category_factory(user=user, name="General", parent=hogar)
        general_auto = expense_category_factory(user=user, name="General", parent=auto)
        for year, month in HISTORY:
            spend(general_hogar, 10000, year, month)
            spend(general_auto, 10000, year, month)
        spend(general_hogar, 20000, 2026, 10)
        spend(general_auto, 10000, 2026, 10)

        assert "General (Hogar)" in texts(insights(user))[0]

    def test_promedia_solo_los_meses_con_gastos(self, user, spend, delivery, super_):
        for month in range(6, 10):
            spend(delivery, 10000, 2026, month)
            spend(super_, 20000, 2026, month)
        spend(delivery, 15000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        assert "los últimos 4 meses" in texts(insights(user))[0]

    def test_gastos_en_dolares_usan_el_monto_en_pesos(
        self, user, baseline, spend, delivery, super_
    ):
        spend(delivery, 10, 2026, 10, currency="USD", exchange_rate=Decimal("1500"))
        spend(super_, 20000, 2026, 10)

        assert "($ 15.000 contra $ 10.000)" in texts(insights(user))[0]


@pytest.mark.django_db
class TestTotalRule:
    def test_total_por_encima_del_promedio(self, user, baseline, spend, delivery, super_):
        spend(delivery, 10000, 2026, 10)
        spend(super_, 30000, 2026, 10)

        result = insights(user)

        total = next(i for i in result.items if i.kind == "total")
        assert total.tone == "warning"
        assert total.text == (
            "En total gastaste 33% más que tu promedio de los últimos 6 meses "
            "($ 40.000 contra $ 30.000)."
        )

    def test_total_por_debajo_ordenado_por_impacto(self, user, baseline, spend, delivery, super_):
        spend(delivery, 5000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        result = insights(user)

        assert [i.kind for i in result.items] == ["category_down", "total"]
        assert result.items[1].text.startswith("En total gastaste 17% menos")

    def test_cambio_total_menor_al_10_por_ciento_no_cuenta(
        self, user, baseline, spend, delivery, super_
    ):
        spend(delivery, 12500, 2026, 10)
        spend(super_, 20000, 2026, 10)

        assert "total" not in [i.kind for i in insights(user).items]


@pytest.mark.django_db
class TestBestMonthRule:
    def test_mejor_mes_de_ahorro_del_anio_va_primero(
        self, user, baseline, spend, earn, delivery, super_
    ):
        for year, month in HISTORY:
            earn(40000, year, month)
        earn(60000, 2026, 10)
        spend(delivery, 5000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        result = insights(user)

        assert result.items[0].kind == "best_month"
        assert result.items[0].text == (
            "Fue tu mejor mes de ahorro del año: ingresaste $ 35.000 más de lo que gastaste."
        )
        assert len(result.items) == 3

    def test_empate_no_es_mejor_mes(self, user, baseline, spend, earn, delivery, super_):
        for year, month in HISTORY:
            earn(40000, year, month)
        earn(40000, 2026, 10)
        spend(delivery, 10000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        assert insights(user) is None

    def test_balance_negativo_no_es_mejor_mes(self, user, baseline, spend, earn, delivery, super_):
        spend(delivery, 10000, 2026, 10)
        spend(super_, 20000, 2026, 10)
        earn(1000, 2026, 10)

        assert insights(user) is None

    def test_no_compara_con_meses_del_anio_anterior(self, user, spend, earn, delivery):
        # En marzo de 2026 solo hay 3 períodos del año: enero, febrero y marzo.
        for month in (10, 11, 12):
            spend(delivery, 10000, 2025, month)
            earn(90000, 2025, month)
        for month in (1, 2):
            spend(delivery, 10000, 2026, month)
            earn(15000, 2026, month)
        spend(delivery, 10000, 2026, 3)
        earn(20000, 2026, 3)

        result = insights(user, today=date(2026, 4, 10))

        assert [i.kind for i in result.items] == ["best_month"]


@pytest.mark.django_db
class TestPeriods:
    def test_respeta_el_inicio_del_mes_financiero(self, user, spend, delivery, super_):
        user.financial_month_start_day = 10
        user.save()
        for year, month in HISTORY:
            spend(delivery, 10000, year, month, day=20)
            spend(super_, 20000, year, month, day=20)
        # Período de octubre: del 10/10 al 09/11. El gasto del 5/10 es de septiembre.
        spend(delivery, 15000, 2026, 11, day=5)
        spend(super_, 20000, 2026, 10, day=12)
        spend(delivery, 99999, 2026, 10, day=5)

        result = insights(user)

        assert result.month == 10
        assert "($ 15.000 contra" in texts(result)[0]

    def test_cruce_de_anio(self, user, spend, delivery, super_):
        for month in range(6, 12):
            spend(delivery, 10000, 2026, month)
            spend(super_, 20000, 2026, month)
        spend(delivery, 15000, 2026, 12)
        spend(super_, 20000, 2026, 12)

        result = insights(user, today=date(2027, 1, 20))

        assert (result.month, result.year) == (12, 2026)
        assert "los últimos 6 meses" in texts(result)[0]

    def test_mes_pasado_seleccionado(self, user, baseline, spend, delivery):
        spend(delivery, 5000, 2026, 9)

        result = build_monthly_insights(user, 9, 2026, TODAY)

        assert result.month == 9
        assert "los últimos 5 meses ($ 15.000 contra $ 10.000)" in texts(result)[0]

    def test_consultas_constantes(
        self, user, baseline, spend, delivery, super_, django_assert_max_num_queries
    ):
        spend(delivery, 15000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        with django_assert_max_num_queries(2):
            insights(user)


@pytest.mark.django_db
class TestHtml:
    def test_escapa_el_nombre_y_marca_los_montos(
        self, user, spend, super_, expense_category_factory
    ):
        rara = expense_category_factory(user=user, name="<b>Ropa</b>")
        for year, month in HISTORY:
            spend(rara, 10000, year, month)
            spend(super_, 20000, year, month)
        spend(rara, 15000, 2026, 10)
        spend(super_, 20000, 2026, 10)

        html = insights(user).items[0].as_html()

        assert "&lt;b&gt;Ropa&lt;/b&gt;" in html
        assert '<span class="sensitive-amount">$ 15.000</span>' in html


@pytest.mark.django_db
class TestDashboardCard:
    def test_muestra_el_resumen_del_periodo_cerrado(self, client, user, spend, delivery, super_):
        today = timezone.localdate()
        for n in range(2, 8):
            day = months_back(today, n)
            spend(delivery, 10000, day.year, day.month)
            spend(super_, 20000, day.year, day.month)
        last = months_back(today, 1)
        spend(delivery, 15000, last.year, last.month)
        spend(super_, 20000, last.year, last.month)
        client.force_login(user)

        response = client.get(reverse("reports:dashboard"))

        assert response.context["monthly_insights"].month == last.month
        content = response.content.decode()
        assert "bi-lightbulb" in content
        assert "Gastaste 50% más en Delivery" in content
        assert '<span class="sensitive-amount">$ 15.000</span>' in content

    def test_usuario_nuevo_no_ve_la_tarjeta(self, client, user):
        client.force_login(user)

        response = client.get(reverse("reports:dashboard"))

        assert response.context["monthly_insights"] is None
        assert "bi-lightbulb" not in response.content.decode()
