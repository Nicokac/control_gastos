from datetime import date
from decimal import Decimal

import pytest

from apps.expenses.models import Expense
from apps.income.models import Income
from apps.notifications import summaries
from apps.notifications.models import DeviceToken, Notification, SummaryKind, SummaryLog
from apps.notifications.summaries import build_period_start_body, send_period_start_notices
from apps.savings.models import RolloverSuggestion, RolloverSuggestionStatus


@pytest.fixture
def pushes(monkeypatch):
    state = {"calls": [], "result": 1}

    def _push(user, title, body, data=None, channel_id=None):
        state["calls"].append(
            {"user": user, "title": title, "body": body, "data": data, "channel_id": channel_id}
        )
        return state["result"]

    monkeypatch.setattr(summaries, "send_push_to_user", _push)
    return state


@pytest.fixture
def device(user):
    return DeviceToken.objects.create(user=user, token="fid-usuario")


@pytest.fixture
def movements(income_category, expense_category):
    def _add(user, day, income="0", expense="0"):
        common = {"user": user, "date": day, "currency": "ARS", "exchange_rate": Decimal("1")}
        if Decimal(income):
            Income.objects.create(
                category=income_category, description="Sueldo", amount=Decimal(income), **common
            )
        if Decimal(expense):
            Expense.objects.create(
                category=expense_category, description="Gasto", amount=Decimal(expense), **common
            )

    return _add


@pytest.mark.django_db
class TestPeriodStartSeleccion:
    def test_avisa_el_primer_dia_si_el_mes_anterior_cerro_con_sobrante(
        self, user, device, movements, pushes
    ):
        movements(user, date(2026, 11, 3), income="1000", expense="400")

        assert send_period_start_notices(date(2026, 12, 1)) == 1

        call = pushes["calls"][0]
        assert call["title"] == "Empezó tu nuevo período"
        assert call["body"] == (
            "Tu período de noviembre 2026 cerró con sobrante. "
            "¿Lo pasás a un ahorro? Lo ves en el inicio."
        )
        assert call["data"] == {"type": "period_start"}
        assert call["channel_id"] == "weekly_summary"
        suggestion = RolloverSuggestion.objects.get(user=user)
        assert suggestion.amount == Decimal("600")
        assert suggestion.status == RolloverSuggestionStatus.PENDING
        log = SummaryLog.objects.get(user=user)
        assert (log.kind, log.period_start, log.pushed, log.emailed) == (
            SummaryKind.PERIOD_START,
            date(2026, 12, 1),
            True,
            False,
        )
        assert Notification.objects.get(user=user).type == "period_start"

    def test_usa_el_dia_de_inicio_del_usuario(self, user, device, movements, pushes):
        user.financial_month_start_day = 10
        user.save()
        movements(user, date(2026, 10, 9), income="5000")
        movements(user, date(2026, 10, 10), income="1000", expense="300")
        movements(user, date(2026, 11, 9), expense="200")

        assert send_period_start_notices(date(2026, 11, 1)) == 0
        assert send_period_start_notices(date(2026, 11, 10)) == 1

        suggestion = RolloverSuggestion.objects.get(user=user)
        assert (suggestion.period_start, suggestion.period_end) == (
            date(2026, 10, 10),
            date(2026, 11, 10),
        )
        assert suggestion.amount == Decimal("500")
        assert "período de octubre 2026" in pushes["calls"][0]["body"]

    def test_no_avisa_otro_dia(self, user, device, movements, pushes):
        movements(user, date(2026, 11, 3), income="1000")

        assert send_period_start_notices(date(2026, 12, 2)) == 0
        assert pushes["calls"] == []

    def test_no_avisa_si_el_periodo_cerro_sin_sobrante(self, user, device, movements, pushes):
        movements(user, date(2026, 11, 3), income="1000", expense="1000")

        assert send_period_start_notices(date(2026, 12, 1)) == 0
        assert not RolloverSuggestion.objects.exists()

    def test_no_avisa_si_ya_decidio_que_hacer_con_el_sobrante(
        self, user, device, movements, pushes
    ):
        movements(user, date(2026, 11, 3), income="1000")
        RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 11, 1),
            period_end=date(2026, 12, 1),
            amount=Decimal("1000"),
            status=RolloverSuggestionStatus.DISMISSED,
        )

        assert send_period_start_notices(date(2026, 12, 1)) == 0

    def test_no_avisa_con_los_resumenes_apagados(self, user, device, movements, pushes):
        user.summaries_enabled = False
        user.save()
        movements(user, date(2026, 11, 3), income="1000")

        assert send_period_start_notices(date(2026, 12, 1)) == 0

    def test_no_avisa_sin_dispositivo_activo(self, user, movements, pushes):
        movements(user, date(2026, 11, 3), income="1000")

        assert send_period_start_notices(date(2026, 12, 1)) == 0
        assert not RolloverSuggestion.objects.exists()


@pytest.mark.django_db
class TestPeriodStartEnvio:
    def test_cada_usuario_con_su_propio_balance(self, user, other_user, device, movements, pushes):
        DeviceToken.objects.create(user=other_user, token="fid-otro")
        movements(user, date(2026, 11, 3), income="1000")
        movements(other_user, date(2026, 11, 3), expense="50")

        assert send_period_start_notices(date(2026, 12, 1)) == 1
        assert pushes["calls"][0]["user"] == user

    def test_dos_ejecuciones_el_mismo_dia_no_duplican(self, user, device, movements, pushes):
        movements(user, date(2026, 11, 3), income="1000")

        assert send_period_start_notices(date(2026, 12, 1)) == 1
        assert send_period_start_notices(date(2026, 12, 1)) == 0
        assert len(pushes["calls"]) == 1
        assert Notification.objects.count() == 1

    def test_sin_entrega_no_registra_y_se_reintenta(self, user, device, movements, pushes):
        movements(user, date(2026, 11, 3), income="1000")
        pushes["result"] = 0

        assert send_period_start_notices(date(2026, 12, 1)) == 0
        assert not SummaryLog.objects.exists()
        assert not Notification.objects.exists()

        pushes["result"] = 1
        assert send_period_start_notices(date(2026, 12, 1)) == 1

    def test_enero_avisa_por_diciembre_del_anio_anterior(self, user, device, movements, pushes):
        movements(user, date(2026, 12, 20), income="1000")

        assert send_period_start_notices(date(2027, 1, 1)) == 1
        assert pushes["calls"][0]["body"] == build_period_start_body(date(2026, 12, 1))
        assert "diciembre 2026" in pushes["calls"][0]["body"]
