from datetime import date
from io import StringIO

from django.core.management import CommandError, call_command

import pytest

from apps.notifications import reminders
from apps.notifications.models import DeviceToken, Notification, RecurringReminderLog
from apps.notifications.reminders import build_reminder_body, send_recurring_reminders
from apps.recurring.models import RecurringExpense

# Hoy simulado: 7/11/2026 -> los recordatorios apuntan al 10/11/2026.
TODAY = date(2026, 11, 7)


@pytest.fixture
def sent_pushes(monkeypatch):
    """Reemplaza el envío real; `result` es lo que devuelve send_push_to_user."""
    state = {"calls": [], "result": 1}

    def _send(user, title, body, data=None):
        state["calls"].append({"user": user, "title": title, "body": body, "data": data})
        return state["result"]

    monkeypatch.setattr(reminders, "send_push_to_user", _send)
    return state


@pytest.fixture
def device(user):
    return DeviceToken.objects.create(user=user, token="fid-usuario")


@pytest.fixture
def make_recurring(user, expense_category):
    def _make(name="Alquiler", due_day=10, owner=None, **kwargs):
        return RecurringExpense.objects.create(
            user=owner or user,
            name=name,
            category=kwargs.pop("category", expense_category),
            due_day=due_day,
            **kwargs,
        )

    return _make


@pytest.mark.django_db
class TestRecurringRemindersSeleccion:
    def test_avisa_gasto_que_vence_en_3_dias(self, device, make_recurring, sent_pushes):
        rec = make_recurring()

        assert send_recurring_reminders(TODAY) == 1

        assert len(sent_pushes["calls"]) == 1
        assert sent_pushes["calls"][0]["body"] == "En 3 días vence Alquiler."
        assert sent_pushes["calls"][0]["data"] == {"type": "recurring_reminder"}
        assert RecurringReminderLog.objects.filter(
            recurring=rec, due_date=date(2026, 11, 10)
        ).exists()

    def test_no_avisa_si_no_vence_en_3_dias(self, device, make_recurring, sent_pushes):
        make_recurring(due_day=11)

        assert send_recurring_reminders(TODAY) == 0
        assert sent_pushes["calls"] == []

    def test_no_avisa_gasto_inactivo(self, device, make_recurring, sent_pushes):
        make_recurring(is_active=False)

        send_recurring_reminders(TODAY)

        assert sent_pushes["calls"] == []

    def test_no_avisa_si_ya_esta_pago_en_el_mes(
        self, user, device, make_recurring, expense_category, expense_factory, sent_pushes
    ):
        rec = make_recurring()
        expense_factory(user, expense_category, recurring=rec, date=date(2026, 11, 2))

        send_recurring_reminders(TODAY)

        assert sent_pushes["calls"] == []

    def test_pago_del_mes_anterior_no_cuenta(
        self, user, device, make_recurring, expense_category, expense_factory, sent_pushes
    ):
        rec = make_recurring()
        expense_factory(user, expense_category, recurring=rec, date=date(2026, 10, 10))

        send_recurring_reminders(TODAY)

        assert len(sent_pushes["calls"]) == 1

    def test_no_avisa_si_empieza_despues_del_vencimiento(self, device, make_recurring, sent_pushes):
        make_recurring(start_date=date(2026, 12, 1))

        send_recurring_reminders(TODAY)

        assert sent_pushes["calls"] == []

    def test_avisa_si_empieza_el_mismo_mes(self, device, make_recurring, sent_pushes):
        make_recurring(start_date=date(2026, 11, 1))

        send_recurring_reminders(TODAY)

        assert len(sent_pushes["calls"]) == 1

    def test_no_avisa_usuario_sin_dispositivo_activo(self, user, make_recurring, sent_pushes):
        DeviceToken.objects.create(user=user, token="fid-inactivo", is_active=False)
        make_recurring()

        send_recurring_reminders(TODAY)

        assert sent_pushes["calls"] == []

    def test_no_avisa_si_el_usuario_desactivo_los_recordatorios(
        self, user, device, make_recurring, sent_pushes
    ):
        user.recurring_reminders_enabled = False
        user.save()
        make_recurring()

        assert send_recurring_reminders(TODAY) == 0
        assert sent_pushes["calls"] == []
        assert not RecurringReminderLog.objects.exists()


@pytest.mark.django_db
class TestRecurringRemindersHistorial:
    def test_guarda_el_aviso_enviado_sin_leer(self, user, device, make_recurring, sent_pushes):
        make_recurring()
        make_recurring(name="Luz")

        send_recurring_reminders(TODAY)

        notification = Notification.objects.get()
        assert notification.user == user
        assert notification.type == "recurring_reminder"
        assert notification.title == "Gastos fijos por vencer"
        assert notification.body == sent_pushes["calls"][0]["body"]
        assert notification.read_at is None

    def test_no_guarda_si_el_push_no_se_entrego(self, device, make_recurring, sent_pushes):
        sent_pushes["result"] = 0
        make_recurring()

        send_recurring_reminders(TODAY)

        assert not Notification.objects.exists()

    def test_no_duplica_si_el_cron_corre_dos_veces(self, device, make_recurring, sent_pushes):
        make_recurring()

        send_recurring_reminders(TODAY)
        send_recurring_reminders(TODAY)

        assert Notification.objects.count() == 1


@pytest.mark.django_db
class TestRecurringRemindersFechas:
    def test_dia_31_vence_el_ultimo_dia_de_un_mes_de_30(self, device, make_recurring, sent_pushes):
        make_recurring(name="Cochera", due_day=31)
        make_recurring(name="Luz", due_day=30)

        send_recurring_reminders(date(2026, 11, 27))

        # Orden por día de vencimiento original: Luz (30) antes que Cochera (31).
        assert sent_pushes["calls"][0]["body"] == "En 3 días vencen Luz y Cochera."

    def test_dias_29_a_31_vencen_el_28_de_febrero(self, device, make_recurring, sent_pushes):
        for day in (29, 30, 31):
            make_recurring(name=f"Gasto {day}", due_day=day)
        make_recurring(name="Gasto 27", due_day=27)

        send_recurring_reminders(date(2027, 2, 25))

        body = sent_pushes["calls"][0]["body"]
        assert body == "En 3 días vencen Gasto 29, Gasto 30 y Gasto 31."

    def test_cambio_de_mes(
        self, user, device, make_recurring, expense_category, expense_factory, sent_pushes
    ):
        rec = make_recurring(due_day=1)
        expense_factory(user, expense_category, recurring=rec, date=date(2027, 1, 1))

        send_recurring_reminders(date(2027, 1, 29))

        assert len(sent_pushes["calls"]) == 1
        assert RecurringReminderLog.objects.get().due_date == date(2027, 2, 1)

    def test_cambio_de_anio(self, device, make_recurring, sent_pushes):
        make_recurring(due_day=2)

        send_recurring_reminders(date(2026, 12, 30))

        assert RecurringReminderLog.objects.get().due_date == date(2027, 1, 2)


@pytest.mark.django_db
class TestRecurringRemindersEnvio:
    def test_agrupa_los_gastos_del_usuario_en_un_solo_push(
        self, device, make_recurring, sent_pushes
    ):
        make_recurring(name="Alquiler")
        make_recurring(name="Luz")
        make_recurring(name="Internet", is_auto_debit=True)

        assert send_recurring_reminders(TODAY) == 1

        assert len(sent_pushes["calls"]) == 1
        assert sent_pushes["calls"][0]["body"] == (
            "En 3 días vencen Alquiler y Luz; se debita automáticamente Internet."
        )
        assert RecurringReminderLog.objects.count() == 3

    def test_un_push_por_usuario_sin_mezclar_gastos(
        self, user, other_user, device, make_recurring, expense_category_factory, sent_pushes
    ):
        DeviceToken.objects.create(user=other_user, token="fid-otro")
        make_recurring(name="Alquiler")
        make_recurring(
            name="Gimnasio",
            owner=other_user,
            category=expense_category_factory(user=other_user, name="Deporte"),
        )

        assert send_recurring_reminders(TODAY) == 2

        bodies = {call["user"].pk: call["body"] for call in sent_pushes["calls"]}
        assert bodies == {
            user.pk: "En 3 días vence Alquiler.",
            other_user.pk: "En 3 días vence Gimnasio.",
        }

    def test_no_reenvia_si_el_cron_corre_dos_veces(self, device, make_recurring, sent_pushes):
        make_recurring()

        send_recurring_reminders(TODAY)
        send_recurring_reminders(TODAY)

        assert len(sent_pushes["calls"]) == 1

    def test_si_no_se_entrego_no_registra_y_reintenta(self, device, make_recurring, sent_pushes):
        make_recurring()
        sent_pushes["result"] = 0

        assert send_recurring_reminders(TODAY) == 0
        assert not RecurringReminderLog.objects.exists()

        sent_pushes["result"] = 1
        send_recurring_reminders(TODAY)

        assert len(sent_pushes["calls"]) == 2
        assert RecurringReminderLog.objects.count() == 1

    def test_usa_hoy_en_hora_local_por_defecto(
        self, device, make_recurring, sent_pushes, monkeypatch
    ):
        monkeypatch.setattr(reminders.timezone, "localdate", lambda: TODAY)
        make_recurring()

        send_recurring_reminders()

        assert len(sent_pushes["calls"]) == 1


class TestBuildReminderBody:
    @staticmethod
    def _rec(name, auto=False):
        return RecurringExpense(name=name, is_auto_debit=auto)

    def test_un_solo_debito_automatico(self):
        assert build_reminder_body([self._rec("Netflix", auto=True)]) == (
            "En 3 días se debita automáticamente Netflix."
        )

    def test_varios_debitos_automaticos(self):
        body = build_reminder_body([self._rec("Netflix", True), self._rec("Spotify", True)])
        assert body == "En 3 días se debitan automáticamente Netflix y Spotify."


@pytest.mark.django_db
class TestSendRecurringRemindersCommand:
    def test_fecha_invalida_falla(self):
        with pytest.raises(CommandError):
            call_command("send_recurring_reminders", "--date", "07/11/2026")

    def test_informa_usuarios_notificados(self, device, make_recurring, sent_pushes):
        make_recurring()
        out = StringIO()

        call_command("send_recurring_reminders", "--date", "2026-11-07", stdout=out)

        assert "Usuarios notificados: 1" in out.getvalue()
