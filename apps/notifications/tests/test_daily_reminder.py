from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from apps.expenses.models import Expense
from apps.notifications import reminders
from apps.notifications.models import DeviceToken, Notification, SummaryKind, SummaryLog
from apps.notifications.reminders import send_daily_reminders

AR = ZoneInfo("America/Argentina/Buenos_Aires")
NIGHT = datetime(2026, 11, 26, 22, 0, tzinfo=AR)


@pytest.fixture
def pushes(monkeypatch):
    state = {"calls": [], "result": 1}

    def _push(user, title, body, data=None, channel_id=None):
        state["calls"].append(
            {"user": user, "title": title, "body": body, "data": data, "channel_id": channel_id}
        )
        return state["result"]

    monkeypatch.setattr(reminders, "send_push_to_user", _push)
    return state


@pytest.fixture
def opted_in(user):
    user.daily_reminder_enabled = True
    user.save()
    DeviceToken.objects.create(user=user, token="fid-usuario")
    return user


@pytest.fixture
def expense_created(expense_category):
    def _add(user, created_at, day=None):
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto",
            amount=Decimal("100"),
            date=day or created_at.date(),
            currency="ARS",
            exchange_rate=Decimal("1"),
        )
        Expense.objects.filter(pk=expense.pk).update(created_at=created_at)
        return expense

    return _add


@pytest.mark.django_db
class TestDailyReminderSeleccion:
    def test_por_defecto_esta_desactivado(self, user):
        assert user.daily_reminder_enabled is False

    def test_avisa_si_no_cargo_ningun_gasto_en_el_dia(self, opted_in, pushes):
        assert send_daily_reminders(NIGHT) == 1

        call = pushes["calls"][0]
        assert call["user"] == opted_in
        assert call["title"] == "¿Cargaste tus gastos de hoy?"
        assert call["body"] == (
            "Todavía no registraste ningún gasto hoy. "
            "Cargalo en un toque antes de que se te olvide."
        )
        assert call["data"] == {"type": "daily_reminder"}
        assert call["channel_id"] == "daily_reminder"
        log = SummaryLog.objects.get(user=opted_in)
        assert (log.kind, log.period_start, log.pushed) == (
            SummaryKind.DAILY_REMINDER,
            date(2026, 11, 26),
            True,
        )
        assert Notification.objects.get(user=opted_in).type == "daily_reminder"

    def test_no_avisa_si_cargo_un_gasto_hoy(self, opted_in, expense_created, pushes):
        expense_created(opted_in, NIGHT.replace(hour=13))

        assert send_daily_reminders(NIGHT) == 0
        assert pushes["calls"] == []

    def test_cuenta_la_carga_de_hoy_aunque_el_gasto_sea_de_otro_dia(
        self, opted_in, expense_created, pushes
    ):
        expense_created(opted_in, NIGHT.replace(hour=9), day=date(2026, 11, 20))

        assert send_daily_reminders(NIGHT) == 0

    def test_un_gasto_de_hoy_cargado_ayer_no_cuenta(self, opted_in, expense_created, pushes):
        expense_created(opted_in, NIGHT - timedelta(days=1), day=date(2026, 11, 26))

        assert send_daily_reminders(NIGHT) == 1

    def test_usa_el_dia_de_argentina_y_no_el_de_utc(self, opted_in, expense_created, pushes):
        # 25/11 23:30 en Argentina es 26/11 02:30 UTC: fue ayer para el usuario.
        expense_created(opted_in, datetime(2026, 11, 25, 23, 30, tzinfo=AR))

        assert send_daily_reminders(NIGHT) == 1

    def test_con_la_preferencia_apagada_no_avisa(self, opted_in, pushes):
        opted_in.daily_reminder_enabled = False
        opted_in.save()

        assert send_daily_reminders(NIGHT) == 0
        assert pushes["calls"] == []

    def test_sin_dispositivo_activo_no_avisa(self, opted_in, pushes):
        DeviceToken.objects.filter(user=opted_in).update(is_active=False)

        assert send_daily_reminders(NIGHT) == 0

    def test_usuario_inactivo_no_recibe(self, opted_in, pushes):
        opted_in.is_active = False
        opted_in.save()

        assert send_daily_reminders(NIGHT) == 0

    def test_el_gasto_de_otro_usuario_no_cuenta(
        self, opted_in, other_user, expense_created, pushes
    ):
        expense_created(other_user, NIGHT.replace(hour=13))

        assert send_daily_reminders(NIGHT) == 1
        assert pushes["calls"][0]["user"] == opted_in


@pytest.mark.django_db
class TestDailyReminderEjecucion:
    def test_doble_ejecucion_no_duplica(self, opted_in, pushes):
        send_daily_reminders(NIGHT)

        assert send_daily_reminders(NIGHT.replace(minute=40)) == 0
        assert len(pushes["calls"]) == 1
        assert Notification.objects.filter(user=opted_in).count() == 1

    def test_si_no_se_entrego_se_reintenta(self, opted_in, pushes):
        pushes["result"] = 0
        assert send_daily_reminders(NIGHT) == 0
        assert not SummaryLog.objects.exists()
        assert not Notification.objects.exists()

        pushes["result"] = 1
        assert send_daily_reminders(NIGHT.replace(minute=30)) == 1

    def test_al_dia_siguiente_vuelve_a_avisar(self, opted_in, pushes):
        send_daily_reminders(NIGHT)

        assert send_daily_reminders(NIGHT + timedelta(days=1)) == 1

    def test_pasada_la_medianoche_no_envia(self, opted_in, pushes):
        # Cron demorado: a las 00:30 "hoy" ya es el día siguiente.
        assert send_daily_reminders(datetime(2026, 11, 27, 0, 30, tzinfo=AR)) == 0
        assert pushes["calls"] == []

    def test_desde_las_20_envia(self, opted_in, pushes):
        assert send_daily_reminders(NIGHT.replace(hour=20)) == 1

    def test_antes_de_las_20_no_envia(self, opted_in, pushes):
        assert send_daily_reminders(NIGHT.replace(hour=19, minute=59)) == 0
