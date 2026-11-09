import calendar
import logging
from collections import defaultdict
from datetime import date, timedelta

from django.utils import timezone

from apps.notifications.models import RecurringReminderLog
from apps.notifications.services import send_push_to_user
from apps.recurring.models import RecurringExpense

logger = logging.getLogger("apps.notifications")

REMINDER_DAYS_BEFORE = 3
REMINDER_TITLE = "Gastos fijos por vencer"


def _effective_due_date(due_day: int, year: int, month: int) -> date:
    """Un gasto con día 31 vence el último día en los meses más cortos."""
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(due_day, last_day))


def _starts_after(recurring, target: date) -> bool:
    start = recurring.start_date
    return start is not None and (start.year, start.month) > (target.year, target.month)


def _join_names(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} y {names[-1]}"


def build_reminder_body(recurrings) -> str:
    manual = [r.name for r in recurrings if not r.is_auto_debit]
    auto = [r.name for r in recurrings if r.is_auto_debit]

    parts = []
    if manual:
        verb = "vence" if len(manual) == 1 else "vencen"
        parts.append(f"{verb} {_join_names(manual)}")
    if auto:
        verb = "se debita" if len(auto) == 1 else "se debitan"
        parts.append(f"{verb} automáticamente {_join_names(auto)}")
    return f"En {REMINDER_DAYS_BEFORE} días {'; '.join(parts)}."


def recurrings_due_on(target: date):
    """Gastos fijos activos de usuarios con dispositivo activo que vencen en `target` y no están pagos."""
    candidates = (
        RecurringExpense.objects.filter(is_active=True, user__device_tokens__is_active=True)
        .exclude(reminder_logs__due_date=target)
        .select_related("user")
        .distinct()
        .order_by("user_id", "due_day", "name")
    )
    return [
        r
        for r in candidates
        if _effective_due_date(r.due_day, target.year, target.month) == target
        and not _starts_after(r, target)
        and not r.is_paid_in(target.month, target.year)
    ]


def send_recurring_reminders(today: date | None = None) -> int:
    """Envía un push agrupado por usuario con los gastos fijos que vencen en 3 días.

    Devuelve la cantidad de usuarios notificados.
    """
    today = today or timezone.localdate()
    target = today + timedelta(days=REMINDER_DAYS_BEFORE)

    by_user = defaultdict(list)
    for recurring in recurrings_due_on(target):
        by_user[recurring.user].append(recurring)

    notified = 0
    for user, recurrings in by_user.items():
        sent = send_push_to_user(
            user,
            title=REMINDER_TITLE,
            body=build_reminder_body(recurrings),
            data={"type": "recurring_reminder"},
        )
        # Sin entregas (credenciales ausentes o todos los dispositivos inválidos) no se
        # registra: el aviso no llegó y puede reintentarse en otra ejecución del día.
        if sent:
            RecurringReminderLog.objects.bulk_create(
                [RecurringReminderLog(recurring=r, due_date=target) for r in recurrings],
                ignore_conflicts=True,
            )
            notified += 1

    logger.info(
        "RECURRING_REMINDERS | target=%s users=%s notified=%s", target, len(by_user), notified
    )
    return notified
