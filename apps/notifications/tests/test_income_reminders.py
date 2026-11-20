from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone

import pytest

from apps.income.models import Income
from apps.notifications import reminders
from apps.notifications.models import DeviceToken, IncomeReminderLog, Notification
from apps.notifications.reminders import build_income_body, send_income_reminders
from apps.recurring_income.models import RecurringIncome

# Hoy simulado: 11/11/2026 -> se avisa lo que se esperaba cobrar el 10/11.
TODAY = date(2026, 11, 11)
CREATED = timezone.make_aware(datetime(2026, 1, 1, 12, 0))


@pytest.fixture
def sent_pushes(monkeypatch):
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
def make_income(user, income_category):
    def _make(name="Sueldo", expected_day=10, owner=None, created=CREATED, **kwargs):
        income = RecurringIncome.objects.create(
            user=owner or user,
            name=name,
            category=kwargs.pop("category", income_category),
            expected_day=expected_day,
            **kwargs,
        )
        RecurringIncome.objects.filter(pk=income.pk).update(created_at=created)
        return income

    return _make


def collect(recurring_income, day):
    return Income.objects.create(
        user=recurring_income.user,
        category=recurring_income.category,
        recurring=recurring_income,
        date=day,
        description="Cobro",
        amount=Decimal("1000"),
        currency="ARS",
        exchange_rate=Decimal("1"),
    )


@pytest.mark.django_db
class TestIncomeRemindersSeleccion:
    def test_avisa_ingreso_esperado_ayer_sin_cobro(self, user, device, make_income, sent_pushes):
        income = make_income()

        assert send_income_reminders(TODAY) == 1

        call = sent_pushes["calls"][0]
        assert call["title"] == "¿Ya cobraste?"
        assert (
            call["body"]
            == "Ayer esperabas cobrar Sueldo. Si ya lo cobraste, registralo en Ingresos."
        )
        assert call["data"] == {"type": "income_expected"}
        assert IncomeReminderLog.objects.filter(
            recurring_income=income, expected_date=date(2026, 11, 10)
        ).exists()
        assert Notification.objects.get(user=user).type == "income_expected"

    def test_no_avisa_si_se_esperaba_otro_dia(self, device, make_income, sent_pushes):
        make_income(expected_day=11)
        make_income(name="Freelance", expected_day=9)

        assert send_income_reminders(TODAY) == 0
        assert sent_pushes["calls"] == []

    def test_no_avisa_si_ya_se_cobro_en_el_mes(self, device, make_income, sent_pushes):
        collect(make_income(), date(2026, 11, 8))

        assert send_income_reminders(TODAY) == 0

    def test_un_cobro_de_otro_mes_no_cuenta(self, device, make_income, sent_pushes):
        collect(make_income(), date(2026, 10, 10))

        assert send_income_reminders(TODAY) == 1

    def test_dia_31_se_espera_el_ultimo_dia_de_un_mes_corto(self, device, make_income, sent_pushes):
        make_income(expected_day=31)

        assert send_income_reminders(date(2026, 12, 1)) == 1
        assert IncomeReminderLog.objects.get().expected_date == date(2026, 11, 30)

    def test_no_avisa_ingreso_inactivo(self, device, make_income, sent_pushes):
        make_income(is_active=False)

        assert send_income_reminders(TODAY) == 0

    def test_no_avisa_ingreso_creado_despues_de_la_fecha_esperada(
        self, device, make_income, sent_pushes
    ):
        # 22:00 de Argentina ya es el 11/11 en UTC: cuenta la fecha local, así que sí avisa.
        make_income(created=timezone.make_aware(datetime(2026, 11, 10, 22, 0)))
        make_income(name="Alquiler cobrado", created=timezone.make_aware(datetime(2026, 11, 11)))

        assert send_income_reminders(TODAY) == 1
        assert sent_pushes["calls"][0]["body"].startswith("Ayer esperabas cobrar Sueldo.")

    def test_no_avisa_con_la_preferencia_apagada(self, user, device, make_income, sent_pushes):
        user.recurring_reminders_enabled = False
        user.save()
        make_income()

        assert send_income_reminders(TODAY) == 0

    def test_no_avisa_sin_dispositivo_activo(self, user, make_income, sent_pushes):
        DeviceToken.objects.create(user=user, token="fid-viejo", is_active=False)
        make_income()

        assert send_income_reminders(TODAY) == 0


@pytest.mark.django_db
class TestIncomeRemindersEnvio:
    def test_agrupa_los_ingresos_de_un_usuario_en_un_aviso(self, device, make_income, sent_pushes):
        make_income()
        make_income(name="Alquiler cobrado")

        assert send_income_reminders(TODAY) == 1
        assert sent_pushes["calls"][0]["body"] == (
            "Ayer esperabas cobrar Alquiler cobrado y Sueldo. "
            "Si ya los cobraste, registralos en Ingresos."
        )
        assert IncomeReminderLog.objects.count() == 2

    def test_cada_usuario_recibe_solo_lo_suyo(
        self, user, other_user, device, make_income, income_category_factory, sent_pushes
    ):
        DeviceToken.objects.create(user=other_user, token="fid-otro")
        make_income()
        make_income(
            name="Honorarios",
            owner=other_user,
            category=income_category_factory(user=other_user, name="Honorarios"),
        )

        assert send_income_reminders(TODAY) == 2
        bodies = {c["user"].pk: c["body"] for c in sent_pushes["calls"]}
        assert "Sueldo" in bodies[user.pk] and "Honorarios" not in bodies[user.pk]
        assert "Honorarios" in bodies[other_user.pk]

    def test_dos_ejecuciones_el_mismo_dia_no_duplican(self, device, make_income, sent_pushes):
        make_income()

        assert send_income_reminders(TODAY) == 1
        assert send_income_reminders(TODAY) == 0
        assert len(sent_pushes["calls"]) == 1
        assert Notification.objects.count() == 1

    def test_sin_entrega_no_registra_y_se_reintenta(self, device, make_income, sent_pushes):
        make_income()
        sent_pushes["result"] = 0

        assert send_income_reminders(TODAY) == 0
        assert not IncomeReminderLog.objects.exists()
        assert not Notification.objects.exists()

        sent_pushes["result"] = 1
        assert send_income_reminders(TODAY) == 1

    def test_el_mes_siguiente_vuelve_a_avisar(self, device, make_income, sent_pushes):
        make_income()

        assert send_income_reminders(TODAY) == 1
        assert send_income_reminders(date(2026, 12, 11)) == 1
        assert IncomeReminderLog.objects.count() == 2


class TestBuildIncomeBody:
    def test_tres_ingresos(self):
        incomes = [RecurringIncome(name=n) for n in ("Sueldo", "Alquiler", "Freelance")]

        assert build_income_body(incomes) == (
            "Ayer esperabas cobrar Sueldo, Alquiler y Freelance. "
            "Si ya los cobraste, registralos en Ingresos."
        )
