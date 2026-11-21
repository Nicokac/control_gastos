"""Detección de gastos que se repiten todos los meses y todavía no son gastos fijos (DT-053)."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from statistics import median

from django.utils import timezone

from apps.categories.rules import normalize_text
from apps.expenses.models import Expense
from apps.recurring.models import DismissedRecurringSuggestion, RecurringExpense

WINDOW_MONTHS = 6
MIN_MONTHS = 3
AMOUNT_TOLERANCE = Decimal("0.20")
NAME_MAX_LENGTH = RecurringExpense._meta.get_field("name").max_length


@dataclass
class RecurringSuggestion:
    key: str
    name: str
    category: object
    due_day: int
    amount: Decimal
    months: int
    expense_ids: list[int]


def _month_index(day: date) -> int:
    return day.year * 12 + day.month - 1


def _trailing_run(expenses, current: int) -> list:
    """Gastos de los meses seguidos (uno por mes) que terminan en el mes actual o el anterior."""
    by_month = defaultdict(list)
    for expense in expenses:
        by_month[_month_index(expense.date)].append(expense)

    last = max(by_month)
    if last < current - 1:
        return []
    run = []
    month = last
    while len(by_month.get(month, [])) == 1:
        run.append(by_month[month][0])
        month -= 1
    return run[::-1]


def _similar_amounts(run) -> bool:
    if len({e.currency for e in run}) > 1:
        return False
    middle = median(e.amount for e in run)
    return all(abs(e.amount - middle) <= middle * AMOUNT_TOLERANCE for e in run)


def find_recurring_suggestions(user, today: date | None = None) -> list[RecurringSuggestion]:
    """Grupos de gastos con la misma descripción, uno por mes durante 3+ meses seguidos y montos parecidos."""
    today = today or timezone.localdate()
    current = _month_index(today)
    first = current - (WINDOW_MONTHS - 1)
    window_start = date(first // 12, first % 12 + 1, 1)

    skip = {normalize_text(name) for name in user.recurring_expenses.values_list("name", flat=True)}
    skip |= set(
        DismissedRecurringSuggestion.objects.filter(user=user).values_list("key", flat=True)
    )

    groups = defaultdict(list)
    expenses = (
        # Los aportes a una meta de ahorro se repiten cada mes, pero no son un gasto fijo.
        Expense.objects.filter(
            user=user, date__gte=window_start, recurring__isnull=True, saving__isnull=True
        )
        .exclude(description="")
        .select_related("category__parent")
        .order_by("date", "id")
    )
    for expense in expenses:
        key = normalize_text(expense.description)
        if key and key not in skip:
            groups[key].append(expense)

    suggestions = []
    for key, group in groups.items():
        run = _trailing_run(group, current)
        if len(run) < MIN_MONTHS or not _similar_amounts(run):
            continue
        last = run[-1]
        suggestions.append(
            RecurringSuggestion(
                key=key,
                name=last.description.strip()[:NAME_MAX_LENGTH],
                category=last.category,
                due_day=last.date.day,
                amount=last.amount_ars,
                months=len(run),
                expense_ids=[e.pk for e in run],
            )
        )
    return sorted(suggestions, key=lambda s: (-s.months, -s.amount, s.key))


def find_suggestion(user, key: str) -> RecurringSuggestion | None:
    return next((s for s in find_recurring_suggestions(user) if s.key == key), None)


def link_suggestion_expenses(suggestion: RecurringSuggestion, recurring) -> int:
    """Vincula los pagos de la sugerencia al gasto fijo creado desde ella.

    La sugerencia se busca antes de crear el gasto fijo: después, su nombre ya la excluye.
    """
    # update() y no save(): vincular pagos viejos no debe disparar alertas de gastos.
    return Expense.objects.filter(
        pk__in=suggestion.expense_ids, user=recurring.user, recurring__isnull=True
    ).update(recurring=recurring)
