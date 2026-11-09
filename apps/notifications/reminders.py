import calendar
import logging
from collections import defaultdict
from datetime import date, timedelta

from django.utils import timezone

from apps.notifications.models import (
    Notification,
    NotificationType,
    RecurringReminderLog,
    ReminderKind,
)
from apps.notifications.services import send_push_to_user
from apps.recurring.models import RecurringExpense

logger = logging.getLogger("apps.notifications")

REMINDER_DAYS_BEFORE = 3
REMINDER_TITLE = "Gastos fijos por vencer"
OVERDUE_TITLE = "Gastos fijos vencidos"


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


def build_overdue_body(recurrings) -> str:
    names = _join_names([r.name for r in recurrings])
    if len(recurrings) == 1:
        return f"Ayer venció {names} y todavía no registraste el pago."
    return f"Ayer vencieron {names} y todavía no registraste los pagos."


def recurrings_due_on(target: date, kind: str = ReminderKind.DUE_SOON):
    """Gastos fijos activos de usuarios con recordatorios y dispositivo activos que vencen en `target` y no están pagos."""
    candidates = (
        RecurringExpense.objects.filter(
            is_active=True,
            user__recurring_reminders_enabled=True,
            user__device_tokens__is_active=True,
        )
        .exclude(
            pk__in=RecurringReminderLog.objects.filter(due_date=target, kind=kind).values(
                "recurring_id"
            )
        )
        .select_related("user")
        .distinct()
        .order_by("user_id", "due_day", "name")
    )
    if kind == ReminderKind.OVERDUE:
        # Igual que status_for: un débito automático se paga solo, nunca queda "vencido".
        candidates = candidates.filter(is_auto_debit=False)
    return [
        r
        for r in candidates
        if _effective_due_date(r.due_day, target.year, target.month) == target
        and not _starts_after(r, target)
        and not r.is_paid_in(target.month, target.year)
    ]


def _send_grouped(target: date, kind: str, notification_type: str, title: str, build_body) -> int:
    by_user = defaultdict(list)
    for recurring in recurrings_due_on(target, kind):
        by_user[recurring.user].append(recurring)

    notified = 0
    for user, recurrings in by_user.items():
        body = build_body(recurrings)
        sent = send_push_to_user(user, title=title, body=body, data={"type": notification_type})
        # Sin entregas (credenciales ausentes o todos los dispositivos inválidos) no se
        # registra: el aviso no llegó y puede reintentarse en otra ejecución del día.
        if sent:
            RecurringReminderLog.objects.bulk_create(
                [RecurringReminderLog(recurring=r, due_date=target, kind=kind) for r in recurrings],
                ignore_conflicts=True,
            )
            Notification.objects.create(user=user, type=notification_type, title=title, body=body)
            notified += 1

    logger.info(
        "RECURRING_REMINDERS | kind=%s target=%s users=%s notified=%s",
        kind,
        target,
        len(by_user),
        notified,
    )
    return notified


def send_recurring_reminders(today: date | None = None) -> int:
    """Envía, agrupados por usuario, los gastos fijos que vencen en 3 días y los que vencieron ayer sin pagarse.

    Devuelve la cantidad de avisos enviados.
    """
    today = today or timezone.localdate()
    due_soon = _send_grouped(
        today + timedelta(days=REMINDER_DAYS_BEFORE),
        ReminderKind.DUE_SOON,
        NotificationType.RECURRING_REMINDER,
        REMINDER_TITLE,
        build_reminder_body,
    )
    overdue = _send_grouped(
        today - timedelta(days=1),
        ReminderKind.OVERDUE,
        NotificationType.RECURRING_OVERDUE,
        OVERDUE_TITLE,
        build_overdue_body,
    )
    return due_soon + overdue
