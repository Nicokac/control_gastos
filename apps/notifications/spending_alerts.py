import logging
from datetime import date
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.core.utils import get_financial_period, get_month_date_range_exclusive
from apps.expenses.models import Expense
from apps.income.models import Income
from apps.notifications.models import (
    DeviceToken,
    Notification,
    NotificationType,
    SpendingAlertKind,
    SpendingAlertLog,
)
from apps.notifications.services import send_push_to_user

logger = logging.getLogger("apps.notifications")

SPENDING_ALERTS_CHANNEL = "spending_alerts"
GLOBAL_TITLE = "Alerta de gastos"
CATEGORY_TITLE = "Límite de gastos superado"


def current_financial_period(today: date, start_day: int) -> tuple[date, date]:
    """Período financiero que contiene `today` (el del mes anterior si todavía no llegó el día de inicio)."""
    if start_day > 1 and today.day < start_day:
        month, year = (12, today.year - 1) if today.month == 1 else (today.month - 1, today.year)
    else:
        month, year = today.month, today.year
    return get_financial_period(month, year, start_day)


def _sum_ars(queryset) -> Decimal:
    return queryset.aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")


def _notify(user, kind, period_start, notification_type, title, body, category=None) -> bool:
    sent = send_push_to_user(
        user,
        title=title,
        body=body,
        data={"type": notification_type},
        channel_id=SPENDING_ALERTS_CHANNEL,
    )
    if not sent:
        return False
    SpendingAlertLog.objects.bulk_create(
        [SpendingAlertLog(user=user, kind=kind, category=category, period_start=period_start)],
        ignore_conflicts=True,
    )
    Notification.objects.create(user=user, type=notification_type, title=title, body=body)
    logger.info(
        "SPENDING_ALERT | user_id=%s kind=%s category_id=%s period_start=%s",
        user.pk,
        kind,
        category.pk if category else None,
        period_start,
    )
    return True


def _check_global(expense, today: date) -> bool:
    user = expense.user
    start, end = current_financial_period(today, user.financial_month_start_day)
    if not start <= expense.date < end:
        return False
    if SpendingAlertLog.objects.filter(
        user=user, kind=SpendingAlertKind.GLOBAL, period_start=start
    ).exists():
        return False

    income = _sum_ars(Income.objects.filter(user=user, date__gte=start, date__lt=end))
    if income <= 0:
        return False
    spent = _sum_ars(Expense.objects.filter(user=user, date__gte=start, date__lt=end))
    if spent * 100 < income * user.alert_threshold:
        return False

    return _notify(
        user,
        SpendingAlertKind.GLOBAL,
        start,
        NotificationType.SPENDING_THRESHOLD,
        GLOBAL_TITLE,
        f"Ya gastaste el {user.alert_threshold}% de tus ingresos de este período.",
    )


def _check_category(expense, today: date) -> bool:
    category = expense.category
    if category is None or category.monthly_alert_threshold is None:
        return False
    # Mes calendario, igual que la etiqueta de límite superado en Categorías.
    start, end = get_month_date_range_exclusive(today.month, today.year)
    if not start <= expense.date < end:
        return False
    user = expense.user
    if SpendingAlertLog.objects.filter(
        user=user, kind=SpendingAlertKind.CATEGORY, category=category, period_start=start
    ).exists():
        return False
    if not category.is_over_alert_threshold(user):
        return False

    return _notify(
        user,
        SpendingAlertKind.CATEGORY,
        start,
        NotificationType.CATEGORY_THRESHOLD,
        CATEGORY_TITLE,
        f"Superaste el límite mensual de {category.name}.",
        category=category,
    )


def check_spending_alerts(expense, today: date | None = None) -> int:
    """Envía las alertas de gastos que el gasto recién guardado haya hecho cruzar. Devuelve cuántas."""
    user = expense.user
    if not user.spending_alerts_enabled:
        return 0
    if not DeviceToken.objects.filter(user=user, is_active=True).exists():
        return 0
    today = today or timezone.localdate()
    return int(_check_global(expense, today)) + int(_check_category(expense, today))
