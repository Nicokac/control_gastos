import logging
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core import signing
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.core.utils import format_currency, get_month_name, send_brevo_email
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.notifications.models import (
    DeviceToken,
    Notification,
    NotificationType,
    SummaryKind,
    SummaryLog,
)
from apps.notifications.services import send_push_to_user
from apps.notifications.spending_alerts import current_financial_period
from apps.users.models import User

logger = logging.getLogger("apps.notifications")

WEEKLY_TITLE = "Tu semana en gastos"
# Canal de Android propio (mobile 1.28.0+38). Los teléfonos con una versión anterior no
# lo tienen y FCM usa el canal por defecto del manifest, el de recordatorios.
WEEKLY_SUMMARY_CHANNEL = "weekly_summary"
BATCH_SIZE = 25
# Brevo free allows ~300 emails/day shared with account emails (verification, password reset).
EMAIL_DAILY_LIMIT = 200
# Monday to Wednesday: a weekly summary that could not go out by then is no longer useful.
WEEKLY_LAST_WEEKDAY = 2
UNSUBSCRIBE_SALT = "notifications.summaries.unsubscribe"


@dataclass
class WeeklySummary:
    start: date
    end: date
    total: Decimal
    count: int
    previous_total: Decimal
    top_category: str
    period_spent: Decimal
    period_income: Decimal


def previous_week(today: date) -> tuple[date, date]:
    """Lunes y lunes siguiente (exclusivo) de la semana anterior a la de `today`."""
    start = today - timedelta(days=today.weekday() + 7)
    return start, start + timedelta(days=7)


def _sum_ars(queryset) -> Decimal:
    return queryset.aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")


def build_weekly_summary(user, start: date, end: date) -> WeeklySummary:
    expenses = Expense.objects.filter(user=user, date__gte=start, date__lt=end)
    totals = expenses.aggregate(total=Sum("amount_ars"), count=Count("id"))
    top = (
        expenses.values("category__name")
        .annotate(total=Sum("amount_ars"))
        .order_by("-total", "category__name")
        .first()
    )
    previous = _sum_ars(
        Expense.objects.filter(user=user, date__gte=start - timedelta(days=7), date__lt=start)
    )
    period_start, period_end = current_financial_period(
        end - timedelta(days=1), user.financial_month_start_day
    )
    return WeeklySummary(
        start=start,
        end=end,
        total=totals["total"] or Decimal("0"),
        count=totals["count"],
        previous_total=previous,
        top_category=(top["category__name"] or "") if top else "",
        period_spent=_sum_ars(
            Expense.objects.filter(user=user, date__gte=period_start, date__lt=end)
        ),
        period_income=_sum_ars(
            Income.objects.filter(user=user, date__gte=period_start, date__lt=period_end)
        ),
    )


def week_label(start: date, end: date) -> str:
    last = end - timedelta(days=1)
    if start.month == last.month:
        return f"del {start.day} al {last.day} de {get_month_name(last.month).lower()}"
    return (
        f"del {start.day} de {get_month_name(start.month).lower()} "
        f"al {last.day} de {get_month_name(last.month).lower()}"
    )


def comparison_text(summary: WeeklySummary) -> str:
    if summary.previous_total <= 0:
        return ""
    change = round((summary.total - summary.previous_total) * 100 / summary.previous_total)
    if change > 0:
        return f"un {change}% más que la semana anterior"
    if change < 0:
        return f"un {-change}% menos que la semana anterior"
    return "lo mismo que la semana anterior"


def period_text(summary: WeeklySummary) -> str:
    spent = format_currency(summary.period_spent)
    if summary.period_income > 0:
        share = round(summary.period_spent * 100 / summary.period_income)
        return f"En el período llevás {spent} gastados, el {share}% de tus ingresos."
    return f"En el período llevás {spent} gastados."


def build_push_body(summary: WeeklySummary) -> str:
    noun = "gasto" if summary.count == 1 else "gastos"
    text = f"Gastaste {format_currency(summary.total)} en {summary.count} {noun}"
    comparison = comparison_text(summary)
    if comparison:
        text += f", {comparison}"
    if summary.top_category:
        text += f". Lo que más pesó: {summary.top_category}"
    return f"{text}."


def unsubscribe_url(user) -> str:
    token = signing.dumps(user.pk, salt=UNSUBSCRIBE_SALT)
    return settings.SITE_URL.rstrip("/") + reverse(
        "users:summaries_unsubscribe", kwargs={"token": token}
    )


def user_from_unsubscribe_token(token: str):
    try:
        pk = signing.loads(token, salt=UNSUBSCRIBE_SALT)
    except signing.BadSignature:
        return None
    return User.objects.filter(pk=pk).first()


def build_email_body(user, summary: WeeklySummary) -> str:
    return render_to_string(
        "notifications/emails/weekly_summary.txt",
        {
            "username": user.first_name or user.username,
            "week": week_label(summary.start, summary.end),
            "total": format_currency(summary.total),
            "count": summary.count,
            "comparison": comparison_text(summary),
            "top_category": summary.top_category,
            "period": period_text(summary),
            "dashboard_url": settings.SITE_URL.rstrip("/") + reverse("reports:dashboard"),
            "unsubscribe_url": unsubscribe_url(user),
        },
    )


def weekly_candidates(start: date, end: date):
    """Usuarios con el resumen activado, gastos en la semana, algún canal y sin resumen entregado."""
    return (
        User.objects.filter(is_active=True, summaries_enabled=True)
        .filter(Exists(Expense.objects.filter(user=OuterRef("pk"), date__gte=start, date__lt=end)))
        .filter(
            Q(email_verified=True)
            | Exists(DeviceToken.objects.filter(user=OuterRef("pk"), is_active=True))
        )
        .exclude(
            Exists(
                SummaryLog.objects.filter(
                    user=OuterRef("pk"), kind=SummaryKind.WEEKLY, period_start=start
                )
            )
        )
        .order_by("pk")
    )


def emails_sent_today(today: date) -> int:
    return SummaryLog.objects.filter(emailed=True, created_at__date=today).count()


def send_weekly_summaries(today: date | None = None, batch_size: int = BATCH_SIZE) -> dict:
    """Envía una tanda de resúmenes semanales y devuelve cuántos se entregaron y cuántos quedan.

    Pensado para llamarse varias veces seguidas: cada request de Render tiene 60 s de límite.
    """
    today = today or timezone.localdate()
    if today.weekday() > WEEKLY_LAST_WEEKDAY:
        return {"sent": 0, "remaining": 0}

    start, end = previous_week(today)
    candidates = weekly_candidates(start, end)
    emails_left = EMAIL_DAILY_LIMIT - emails_sent_today(today)

    sent = 0
    for user in candidates[:batch_size]:
        summary = build_weekly_summary(user, start, end)
        push_body = build_push_body(summary)
        pushed = bool(
            send_push_to_user(
                user,
                title=WEEKLY_TITLE,
                body=push_body,
                data={"type": NotificationType.WEEKLY_SUMMARY},
                channel_id=WEEKLY_SUMMARY_CHANNEL,
            )
        )
        emailed = False
        if user.email_verified and user.email and emails_left > 0:
            emailed = send_brevo_email(
                user.email,
                f"Tu semana {week_label(start, end)} — Control de Gastos",
                build_email_body(user, summary),
            )
            emails_left -= emailed
        # Nothing delivered (email cap reached, no devices, provider down): retried on a later run.
        if not (pushed or emailed):
            continue
        SummaryLog.objects.create(
            user=user,
            kind=SummaryKind.WEEKLY,
            period_start=start,
            pushed=pushed,
            emailed=emailed,
        )
        Notification.objects.create(
            user=user, type=NotificationType.WEEKLY_SUMMARY, title=WEEKLY_TITLE, body=push_body
        )
        sent += 1

    remaining = candidates.count()
    logger.info("WEEKLY_SUMMARY | week_start=%s sent=%s remaining=%s", start, sent, remaining)
    return {"sent": sent, "remaining": remaining}
