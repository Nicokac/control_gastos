import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.expenses.models import Expense

logger = logging.getLogger("apps.notifications")


def _check_after_commit(expense):
    from apps.notifications.spending_alerts import check_spending_alerts

    # Corre después de guardar el gasto: un error de Firebase no puede convertir en error
    # una carga que ya quedó registrada.
    try:
        check_spending_alerts(expense)
    except Exception:
        logger.exception("SPENDING_ALERT_FAILED | expense_id=%s", expense.pk)


@receiver(post_save, sender=Expense, dispatch_uid="notifications_spending_alerts")
def expense_saved(sender, instance, **kwargs):
    transaction.on_commit(lambda: _check_after_commit(instance))
