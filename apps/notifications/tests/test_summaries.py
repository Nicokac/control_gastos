from datetime import date
from decimal import Decimal
from urllib.parse import urlparse

from django.urls import reverse

import pytest

from apps.expenses.models import Expense
from apps.income.models import Income
from apps.notifications import summaries
from apps.notifications.models import DeviceToken, Notification, SummaryKind, SummaryLog
from apps.notifications.summaries import (
    build_email_body,
    build_push_body,
    build_weekly_summary,
    previous_week,
    send_weekly_summaries,
    unsubscribe_url,
    week_label,
)

# Lunes 16/11/2026: el resumen cubre del lunes 9 al domingo 15.
MONDAY = date(2026, 11, 16)
WEEK_START = date(2026, 11, 9)
WEEK_END = date(2026, 11, 16)


@pytest.fixture
def channels(monkeypatch):
    """Reemplaza push y email reales; `push` y `email` son lo que devuelve cada envío."""
    state = {"pushes": [], "emails": [], "push": 1, "email": True}

    def _push(user, title, body, data=None, channel_id=None):
        state["pushes"].append(
            {"user": user, "title": title, "body": body, "data": data, "channel_id": channel_id}
        )
        return state["push"]

    def _email(to_email, subject, body):
        state["emails"].append({"to": to_email, "subject": subject, "body": body})
        return state["email"]

    monkeypatch.setattr(summaries, "send_push_to_user", _push)
    monkeypatch.setattr(summaries, "send_brevo_email", _email)
    return state


@pytest.fixture
def spend(expense_category):
    def _spend(user, day, amount, category=None, description="Gasto"):
        return Expense.objects.create(
            user=user,
            category=category or expense_category,
            date=day,
            description=description,
            amount=Decimal(amount),
            currency="ARS",
            exchange_rate=Decimal("1"),
        )

    return _spend


@pytest.fixture
def device(user):
    return DeviceToken.objects.create(user=user, token="fid-usuario")


@pytest.fixture
def verified(user):
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    return user


class TestPreviousWeek:
    @pytest.mark.parametrize("today", [date(2026, 11, 16), date(2026, 11, 18), date(2026, 11, 22)])
    def test_any_day_points_to_previous_monday_to_sunday(self, today):
        assert previous_week(today) == (WEEK_START, WEEK_END)

    def test_week_crossing_year(self):
        assert previous_week(date(2027, 1, 4)) == (date(2026, 12, 28), date(2027, 1, 4))


class TestWeekLabel:
    def test_same_month(self):
        assert week_label(WEEK_START, WEEK_END) == "del 9 al 15 de noviembre"

    def test_crossing_month(self):
        start, end = previous_week(date(2026, 11, 2))

        assert week_label(start, end) == "del 26 de octubre al 1 de noviembre"


@pytest.mark.django_db
class TestBuildWeeklySummary:
    def test_totals_only_count_the_week(self, user, spend):
        spend(user, date(2026, 11, 8), "999")
        spend(user, WEEK_START, "1000")
        spend(user, date(2026, 11, 15), "500")
        spend(user, WEEK_END, "777")

        summary = build_weekly_summary(user, WEEK_START, WEEK_END)

        assert summary.total == Decimal("1500")
        assert summary.count == 2
        assert summary.previous_total == Decimal("999")

    def test_top_category_is_the_heaviest(self, user, spend, expense_category_factory):
        other = expense_category_factory(user, name="Supermercado")
        spend(user, WEEK_START, "100")
        spend(user, WEEK_START, "80", category=other)
        spend(user, WEEK_START, "80", category=other)

        summary = build_weekly_summary(user, WEEK_START, WEEK_END)

        assert summary.top_category == "Supermercado"

    def test_period_uses_financial_month(self, user, spend, income_category):
        user.financial_month_start_day = 10
        user.save(update_fields=["financial_month_start_day"])
        spend(user, date(2026, 11, 9), "300")
        spend(user, date(2026, 11, 10), "200")
        Income.objects.create(
            user=user,
            category=income_category,
            date=date(2026, 11, 10),
            description="Sueldo",
            amount=Decimal("1000"),
            currency="ARS",
            exchange_rate=Decimal("1"),
        )

        summary = build_weekly_summary(user, WEEK_START, WEEK_END)

        assert summary.period_spent == Decimal("200")
        assert summary.period_income == Decimal("1000")


@pytest.mark.django_db
class TestMessages:
    def summary(self, user, spend, previous=None):
        spend(user, WEEK_START, "1100")
        if previous:
            spend(user, date(2026, 11, 2), previous)
        return build_weekly_summary(user, WEEK_START, WEEK_END)

    def test_push_with_more_than_last_week(self, user, spend):
        body = build_push_body(self.summary(user, spend, previous="1000"))

        assert body == (
            "Gastaste $ 1.100,00 en 1 gasto, un 10% más que la semana anterior. "
            "Lo que más pesó: Alimentación."
        )

    def test_push_with_less_than_last_week(self, user, spend):
        body = build_push_body(self.summary(user, spend, previous="2200"))

        assert "un 50% menos que la semana anterior" in body

    def test_push_without_previous_week_has_no_comparison(self, user, spend):
        body = build_push_body(self.summary(user, spend))

        assert body == "Gastaste $ 1.100,00 en 1 gasto. Lo que más pesó: Alimentación."

    def test_email_shows_income_share_and_links(self, user, spend, income_category):
        Income.objects.create(
            user=user,
            category=income_category,
            date=date(2026, 11, 1),
            description="Sueldo",
            amount=Decimal("4400"),
            currency="ARS",
            exchange_rate=Decimal("1"),
        )

        body = build_email_body(user, self.summary(user, spend))

        assert "Así fue tu semana del 9 al 15 de noviembre" in body
        assert "el 25% de tus ingresos" in body
        assert unsubscribe_url(user) in body
        assert reverse("reports:dashboard") in body

    def test_email_does_not_escape_category_names(self, user, spend, expense_category_factory):
        category = expense_category_factory(user, name="Bares & cafés")
        spend(user, WEEK_START, "100", category=category)

        body = build_email_body(user, build_weekly_summary(user, WEEK_START, WEEK_END))

        assert "Bares & cafés" in body
        assert "&amp;" not in body


@pytest.mark.django_db
class TestSendWeeklySummaries:
    def test_sends_push_and_email(self, verified, device, spend, channels):
        spend(verified, WEEK_START, "1000")

        result = send_weekly_summaries(MONDAY)

        assert result == {"sent": 1, "remaining": 0}
        assert len(channels["pushes"]) == 1
        assert channels["pushes"][0]["data"] == {"type": "weekly_summary"}
        assert channels["pushes"][0]["channel_id"] == "weekly_summary"
        assert channels["emails"][0]["to"] == verified.email
        log = SummaryLog.objects.get(user=verified)
        assert (log.kind, log.period_start, log.pushed, log.emailed) == (
            SummaryKind.WEEKLY,
            WEEK_START,
            True,
            True,
        )
        assert Notification.objects.filter(user=verified, type="weekly_summary").count() == 1

    def test_unverified_email_only_gets_push(self, user, device, spend, channels):
        spend(user, WEEK_START, "1000")

        send_weekly_summaries(MONDAY)

        assert len(channels["pushes"]) == 1
        assert channels["emails"] == []
        assert SummaryLog.objects.get(user=user).emailed is False

    def test_verified_without_device_gets_email(self, verified, spend, channels):
        channels["push"] = 0
        spend(verified, WEEK_START, "1000")

        assert send_weekly_summaries(MONDAY)["sent"] == 1
        assert SummaryLog.objects.get(user=verified).pushed is False

    def test_user_without_channels_is_skipped(self, user, spend, channels):
        spend(user, WEEK_START, "1000")

        assert send_weekly_summaries(MONDAY) == {"sent": 0, "remaining": 0}
        assert channels["pushes"] == []

    def test_week_without_expenses_sends_nothing(self, verified, device, spend, channels):
        spend(verified, date(2026, 11, 8), "1000")

        assert send_weekly_summaries(MONDAY) == {"sent": 0, "remaining": 0}

    def test_disabled_preference_sends_nothing(self, verified, device, spend, channels):
        verified.summaries_enabled = False
        verified.save(update_fields=["summaries_enabled"])
        spend(verified, WEEK_START, "1000")

        assert send_weekly_summaries(MONDAY)["sent"] == 0

    def test_second_run_does_not_repeat(self, verified, device, spend, channels):
        spend(verified, WEEK_START, "1000")
        send_weekly_summaries(MONDAY)

        assert send_weekly_summaries(date(2026, 11, 17)) == {"sent": 0, "remaining": 0}
        assert len(channels["pushes"]) == 1

    def test_failed_delivery_is_retried(self, verified, device, spend, channels):
        spend(verified, WEEK_START, "1000")
        channels["push"], channels["email"] = 0, False

        assert send_weekly_summaries(MONDAY) == {"sent": 0, "remaining": 1}
        assert not SummaryLog.objects.exists()

        channels["push"] = 1
        assert send_weekly_summaries(date(2026, 11, 17))["sent"] == 1

    def test_wednesday_still_sends(self, verified, device, spend, channels):
        spend(verified, WEEK_START, "1000")

        assert send_weekly_summaries(date(2026, 11, 18))["sent"] == 1

    def test_thursday_gives_up(self, verified, device, spend, channels):
        spend(verified, WEEK_START, "1000")

        assert send_weekly_summaries(date(2026, 11, 19)) == {"sent": 0, "remaining": 0}

    def test_batches(self, verified, other_user, spend, channels, expense_category_factory):
        DeviceToken.objects.create(user=other_user, token="fid-otro")
        spend(verified, WEEK_START, "1000")
        spend(
            other_user,
            WEEK_START,
            "1000",
            category=expense_category_factory(other_user, name="Otra"),
        )

        assert send_weekly_summaries(MONDAY, batch_size=1) == {"sent": 1, "remaining": 1}
        assert send_weekly_summaries(MONDAY, batch_size=1) == {"sent": 1, "remaining": 0}

    def test_daily_email_limit(
        self, verified, other_user, spend, channels, monkeypatch, expense_category_factory
    ):
        monkeypatch.setattr(summaries, "EMAIL_DAILY_LIMIT", 1)
        channels["push"] = 0
        other_user.email_verified = True
        other_user.save(update_fields=["email_verified"])
        spend(verified, WEEK_START, "1000")
        spend(
            other_user,
            WEEK_START,
            "1000",
            category=expense_category_factory(other_user, name="Otra"),
        )

        assert send_weekly_summaries(MONDAY) == {"sent": 1, "remaining": 1}
        assert len(channels["emails"]) == 1


@pytest.mark.django_db
class TestUnsubscribe:
    def url(self, user):
        return urlparse(unsubscribe_url(user)).path

    def test_get_only_asks_for_confirmation(self, client, user):
        response = client.get(self.url(user))

        assert response.status_code == 200
        assert "¿Dejar de recibir el resumen semanal?" in response.content.decode()
        user.refresh_from_db()
        assert user.summaries_enabled is True

    def test_post_disables_without_login(self, client, user):
        response = client.post(self.url(user))

        assert "No vas a recibir más el resumen semanal" in response.content.decode()
        user.refresh_from_db()
        assert user.summaries_enabled is False

    def test_works_while_logged_in(self, authenticated_client, user):
        response = authenticated_client.post(self.url(user))

        assert "No vas a recibir más el resumen semanal" in response.content.decode()

    def test_tampered_token_is_rejected(self, client, user):
        url = reverse("users:summaries_unsubscribe", kwargs={"token": f"{user.pk}:falso"})

        response = client.post(url)

        assert "Link inválido" in response.content.decode()
        user.refresh_from_db()
        assert user.summaries_enabled is True


@pytest.mark.django_db
class TestSummariesCron:
    url = "/api/v1/notifications/cron/summaries/"
    secret = "cron-secret-de-prueba"  # pragma: allowlist secret

    def test_requires_secret(self, client, settings):
        settings.CRON_SECRET = self.secret

        assert client.post(self.url, HTTP_X_CRON_SECRET=self.secret + "-otro").status_code == 403

    def test_empty_secret_is_rejected(self, client, settings):
        settings.CRON_SECRET = ""

        assert client.post(self.url, HTTP_X_CRON_SECRET="").status_code == 403

    def test_returns_batch_result(self, client, settings, monkeypatch):
        settings.CRON_SECRET = self.secret
        monkeypatch.setattr(
            "apps.api.v1.views.notifications.send_weekly_summaries",
            lambda: {"sent": 3, "remaining": 2},
        )

        response = client.post(self.url, HTTP_X_CRON_SECRET=self.secret)

        assert response.status_code == 200
        assert response.json() == {"sent": 3, "remaining": 2}


@pytest.mark.django_db
class TestSummariesPreference:
    def test_profile_form_turns_it_off(self, authenticated_client, user):
        data = {
            "first_name": "",
            "last_name": "",
            "email": user.email,
            "default_currency": user.default_currency,
            "alert_threshold": user.alert_threshold,
            "financial_month_start_day": user.financial_month_start_day,
        }

        authenticated_client.post(reverse("users:profile"), data)

        user.refresh_from_db()
        assert user.summaries_enabled is False

    def test_api_profile_exposes_it(self, user):
        from apps.api.v1.serializers.auth import UserProfileSerializer

        assert UserProfileSerializer(user).data["summaries_enabled"] is True
