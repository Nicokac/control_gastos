from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

import pytest

from apps.notifications import spending_alerts
from apps.notifications.models import DeviceToken, Notification, SpendingAlertLog
from apps.notifications.spending_alerts import check_spending_alerts, current_financial_period


@pytest.fixture
def sent_pushes(monkeypatch):
    state = {"calls": [], "result": 1}

    def _send(user, title, body, data=None, channel_id=None):
        state["calls"].append(
            {"user": user, "title": title, "body": body, "data": data, "channel_id": channel_id}
        )
        return state["result"]

    monkeypatch.setattr(spending_alerts, "send_push_to_user", _send)
    return state


@pytest.fixture
def device(user):
    return DeviceToken.objects.create(user=user, token="fid-usuario")


@pytest.fixture
def spend(user, expense_category, expense_factory):
    def _spend(amount, category=None, day=None):
        return expense_factory(
            user,
            category or expense_category,
            amount=Decimal(amount),
            date=day or timezone.localdate(),
        )

    return _spend


@pytest.fixture
def earn(user, income_category, income_factory):
    def _earn(amount, day=None):
        return income_factory(
            user, income_category, amount=Decimal(amount), date=day or timezone.localdate()
        )

    return _earn


def _types(state):
    return [c["data"]["type"] for c in state["calls"]]


@pytest.mark.django_db
class TestGlobalSpendingAlert:
    def test_avisa_al_cruzar_el_umbral_de_ingresos(self, device, earn, spend, sent_pushes):
        earn("1000")
        expense = spend("800")

        assert check_spending_alerts(expense) == 1

        call = sent_pushes["calls"][0]
        assert call["title"] == "Alerta de gastos"
        assert call["body"] == "Ya gastaste el 80% de tus ingresos de este período."
        assert call["data"] == {"type": "spending_threshold"}
        assert call["channel_id"] == "spending_alerts"
        assert Notification.objects.get().type == "spending_threshold"

    def test_no_avisa_por_debajo_del_umbral(self, device, earn, spend, sent_pushes):
        earn("1000")
        expense = spend("799.99")

        assert check_spending_alerts(expense) == 0
        assert sent_pushes["calls"] == []

    def test_usa_el_umbral_configurado_por_el_usuario(self, user, device, earn, spend, sent_pushes):
        user.alert_threshold = 50
        user.save()
        earn("1000")
        expense = spend("500")

        check_spending_alerts(expense)

        assert sent_pushes["calls"][0]["body"] == (
            "Ya gastaste el 50% de tus ingresos de este período."
        )

    def test_sin_ingresos_no_avisa(self, device, spend, sent_pushes):
        expense = spend("5000")

        assert check_spending_alerts(expense) == 0

    def test_avisa_una_sola_vez_por_periodo(self, device, earn, spend, sent_pushes):
        earn("1000")
        check_spending_alerts(spend("800"))
        check_spending_alerts(spend("100"))

        assert len(sent_pushes["calls"]) == 1
        assert SpendingAlertLog.objects.count() == 1

    def test_si_no_se_entrego_lo_reintenta_con_el_proximo_gasto(
        self, device, earn, spend, sent_pushes
    ):
        earn("1000")
        sent_pushes["result"] = 0
        check_spending_alerts(spend("800"))
        sent_pushes["result"] = 1
        check_spending_alerts(spend("10"))

        assert len(sent_pushes["calls"]) == 2
        assert SpendingAlertLog.objects.count() == 1
        assert Notification.objects.count() == 1

    def test_un_gasto_de_otro_periodo_no_dispara(self, device, earn, spend, sent_pushes):
        earn("1000")
        spend("900")
        viejo = spend("10", day=timezone.localdate() - timedelta(days=70))

        assert check_spending_alerts(viejo) == 0

    def test_ingresos_de_otro_usuario_no_cuentan(
        self, device, other_user, income_category, income_factory, earn, spend, sent_pushes
    ):
        income_factory(other_user, income_category, amount=Decimal("100000"))
        earn("1000")
        expense = spend("800")

        assert check_spending_alerts(expense) == 1


@pytest.mark.django_db
class TestCategorySpendingAlert:
    @pytest.fixture
    def limited(self, user, expense_category_factory):
        return expense_category_factory(
            user=user, name="Delivery", monthly_alert_threshold=Decimal("500")
        )

    def test_avisa_al_superar_el_limite_de_la_subcategoria(
        self, device, limited, spend, sent_pushes
    ):
        spend("300", category=limited)
        expense = spend("200", category=limited)

        assert check_spending_alerts(expense) == 1

        call = sent_pushes["calls"][0]
        assert call["title"] == "Límite de gastos superado"
        assert call["body"] == "Superaste el límite mensual de Delivery."
        assert call["data"] == {"type": "category_threshold"}
        assert call["channel_id"] == "spending_alerts"

    def test_no_avisa_por_debajo_del_limite(self, device, limited, spend, sent_pushes):
        expense = spend("499", category=limited)

        assert check_spending_alerts(expense) == 0

    def test_subcategoria_sin_limite_no_avisa(self, device, spend, sent_pushes):
        expense = spend("100000")

        assert check_spending_alerts(expense) == 0

    def test_una_vez_por_mes_y_por_subcategoria(
        self, user, device, limited, expense_category_factory, spend, sent_pushes
    ):
        otra = expense_category_factory(
            user=user, name="Salidas", monthly_alert_threshold=Decimal("100")
        )
        check_spending_alerts(spend("600", category=limited))
        check_spending_alerts(spend("50", category=limited))
        check_spending_alerts(spend("150", category=otra))

        assert [c["body"] for c in sent_pushes["calls"]] == [
            "Superaste el límite mensual de Delivery.",
            "Superaste el límite mensual de Salidas.",
        ]

    def test_un_gasto_de_otro_mes_no_dispara(self, device, limited, spend, sent_pushes):
        spend("600", category=limited)
        viejo = spend("10", category=limited, day=timezone.localdate() - timedelta(days=40))

        assert check_spending_alerts(viejo) == 0

    def test_global_y_subcategoria_en_el_mismo_gasto(
        self, device, limited, earn, spend, sent_pushes
    ):
        earn("1000")
        expense = spend("900", category=limited)

        assert check_spending_alerts(expense) == 2
        assert _types(sent_pushes) == ["spending_threshold", "category_threshold"]


@pytest.mark.django_db
class TestSpendingAlertsPreconditions:
    def test_preferencia_apagada_no_avisa(self, user, device, earn, spend, sent_pushes):
        user.spending_alerts_enabled = False
        user.save()
        earn("1000")

        assert check_spending_alerts(spend("900")) == 0
        assert sent_pushes["calls"] == []

    def test_sin_dispositivo_activo_no_avisa(self, earn, spend, sent_pushes):
        earn("1000")

        assert check_spending_alerts(spend("900")) == 0
        assert sent_pushes["calls"] == []


@pytest.mark.django_db
class TestSpendingAlertsSignal:
    def test_guardar_un_gasto_dispara_la_alerta(
        self, device, earn, spend, sent_pushes, django_capture_on_commit_callbacks
    ):
        earn("1000")
        with django_capture_on_commit_callbacks(execute=True):
            spend("800")

        assert _types(sent_pushes) == ["spending_threshold"]

    def test_editar_un_gasto_tambien_dispara(
        self, device, earn, spend, sent_pushes, django_capture_on_commit_callbacks
    ):
        earn("1000")
        expense = spend("100")
        with django_capture_on_commit_callbacks(execute=True):
            expense.amount = Decimal("800")
            expense.save()

        assert _types(sent_pushes) == ["spending_threshold"]

    def test_un_error_al_avisar_no_rompe_el_guardado(
        self, device, earn, spend, monkeypatch, django_capture_on_commit_callbacks
    ):
        def _boom(expense):
            raise RuntimeError("Firebase caido")

        monkeypatch.setattr(spending_alerts, "check_spending_alerts", _boom)
        earn("1000")
        with django_capture_on_commit_callbacks(execute=True):
            expense = spend("800")

        assert expense.pk is not None


class TestCurrentFinancialPeriod:
    def test_mes_calendario_si_empieza_el_dia_1(self):
        assert current_financial_period(date(2026, 11, 9), 1) == (
            date(2026, 11, 1),
            date(2026, 12, 1),
        )

    def test_despues_del_dia_de_inicio_es_el_periodo_de_este_mes(self):
        assert current_financial_period(date(2026, 11, 15), 10) == (
            date(2026, 11, 10),
            date(2026, 12, 10),
        )

    def test_antes_del_dia_de_inicio_es_el_periodo_del_mes_anterior(self):
        assert current_financial_period(date(2026, 11, 5), 10) == (
            date(2026, 10, 10),
            date(2026, 11, 10),
        )

    def test_antes_del_dia_de_inicio_en_enero_vuelve_a_diciembre(self):
        assert current_financial_period(date(2027, 1, 5), 10) == (
            date(2026, 12, 10),
            date(2027, 1, 10),
        )
