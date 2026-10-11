"""
Servicios de ahorro: traslado de sobrante de período financiero (DT-067).
"""

from decimal import Decimal

from django.db.models import Sum

from apps.core.utils import get_financial_period
from apps.expenses.models import Expense
from apps.income.models import Income

from .models import MovementType, RolloverSuggestion, SavingMovement


def get_period_balance(user, period_start, period_end) -> Decimal:
    """Calcula el balance (ingresos - gastos - depósitos a ahorro) de un período."""
    income_total = Income.objects.filter(
        user=user, date__gte=period_start, date__lt=period_end
    ).aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")
    expense_total = Expense.objects.filter(
        user=user, date__gte=period_start, date__lt=period_end
    ).aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")
    savings_deposits_total = SavingMovement.objects.filter(
        saving__user=user,
        type=MovementType.DEPOSIT,
        date__gte=period_start,
        date__lt=period_end,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    return income_total - expense_total - savings_deposits_total


def get_previous_period(month: int, year: int, start_day: int):
    """Retorna (period_start, period_end) del período financiero inmediatamente anterior."""
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    return get_financial_period(prev_month, prev_year, start_day)


def get_or_create_rollover_suggestion(user, month: int, year: int, start_day: int = 1):
    """
    Obtiene (o crea si corresponde) la sugerencia de traslado de sobrante
    para el período financiero inmediatamente anterior a (month, year).

    Solo se crea una sugerencia nueva si el período anterior cerró con
    balance positivo. Si el balance no es positivo, no hay nada que sugerir
    y se retorna None. Si ya existe una sugerencia para ese período
    (en cualquier estado), se retorna sin volver a evaluarla.
    """
    period_start, period_end = get_previous_period(month, year, start_day)

    existing = RolloverSuggestion.objects.filter(
        user=user, period_start=period_start, period_end=period_end
    ).first()
    if existing is not None:
        return existing

    balance = get_period_balance(user, period_start, period_end)
    if balance <= 0:
        return None

    return RolloverSuggestion.objects.create(
        user=user,
        period_start=period_start,
        period_end=period_end,
        amount=balance,
    )


def get_dismissed_amount_for_current_period(user, month: int, year: int, start_day: int = 1):
    """
    Retorna el monto de una sugerencia DESCARTADA cuyo período terminó justo
    donde empieza el período (month, year), o None si no corresponde.

    Se usa para mostrar "Disponible este mes" una sola vez, en el período
    inmediatamente siguiente al descarte.
    """
    from .models import RolloverSuggestionStatus

    current_start, _ = get_financial_period(month, year, start_day)

    suggestion = RolloverSuggestion.objects.filter(
        user=user,
        period_end=current_start,
        status=RolloverSuggestionStatus.DISMISSED,
    ).first()

    return suggestion.amount if suggestion else None
