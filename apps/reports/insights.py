"""Observaciones automáticas sobre el último período cerrado (DT-056)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils.html import format_html

from apps.core.utils import get_financial_period, get_month_name
from apps.expenses.models import Expense
from apps.income.models import Income

WINDOW = 6
MIN_HISTORY = 3
CATEGORY_CHANGE = Decimal("0.25")
CATEGORY_MIN_SHARE = Decimal("0.05")
TOTAL_CHANGE = Decimal("0.10")
MAX_INSIGHTS = 3
# Mismo marcador que usa la app cuando se ocultan los montos (SensitiveText).
HIDDEN_AMOUNT = "••••••"


@dataclass(frozen=True)
class Insight:
    kind: str
    tone: str
    message: str
    args: tuple
    score: Decimal = Decimal("0")

    def _render(self, money) -> str:
        return self.message.format(*(money(a) if isinstance(a, Decimal) else a for a in self.args))

    @property
    def text(self) -> str:
        return self._render(_money)

    @property
    def masked_text(self) -> str:
        return self._render(lambda _: HIDDEN_AMOUNT)

    def as_html(self):
        return format_html(
            self.message,
            *(
                format_html('<span class="sensitive-amount">{}</span>', _money(a))
                if isinstance(a, Decimal)
                else a
                for a in self.args
            ),
        )


@dataclass(frozen=True)
class MonthlyInsights:
    month: int
    year: int
    items: list

    @property
    def label(self) -> str:
        return get_month_name(self.month)


def _money(amount: Decimal) -> str:
    return "$ " + f"{round(amount):,}".replace(",", ".")


def _step_back(month: int, year: int) -> tuple[int, int]:
    return (12, year - 1) if month == 1 else (month - 1, year)


def last_closed_period(month: int, year: int, start_day: int, today: date) -> tuple[int, int]:
    """Mes del período que se resume: el seleccionado si ya cerró, si no el último cerrado."""
    if (month, year) == (today.month, today.year):
        month, year = _step_back(month, year)
    while get_financial_period(month, year, start_day)[1] > today:
        month, year = _step_back(month, year)
    return month, year


def _percent(current: Decimal, average: Decimal) -> int:
    return round(abs(current - average) * 100 / average)


def _months(count: int) -> str:
    return f"los últimos {count} meses"


def _category_insights(rows, target, history, total) -> list[Insight]:
    names = [row["name"] for row in rows]
    insights = []
    for row in rows:
        current = row["totals"][target]
        average = sum(row["totals"][p] for p in history) / len(history)
        if average <= 0:
            continue
        diff = current - average
        if abs(diff) < total * CATEGORY_MIN_SHARE:
            continue
        name = row["name"]
        if names.count(name) > 1 and row["group"]:
            name = f"{name} ({row['group']})"
        score = abs(diff) / total
        if diff >= average * CATEGORY_CHANGE:
            insights.append(
                Insight(
                    "category_up",
                    "warning",
                    "Gastaste {}% más en {} que tu promedio de {} ({} contra {}).",
                    (_percent(current, average), name, _months(len(history)), current, average),
                    score,
                )
            )
        elif current == 0:
            insights.append(
                Insight(
                    "category_down",
                    "positive",
                    "No gastaste en {}, cuando tu promedio de {} es de {}.",
                    (name, _months(len(history)), average),
                    score,
                )
            )
        elif -diff >= average * CATEGORY_CHANGE:
            insights.append(
                Insight(
                    "category_down",
                    "positive",
                    "Gastaste {}% menos en {} que tu promedio de {} ({} contra {}).",
                    (_percent(current, average), name, _months(len(history)), current, average),
                    score,
                )
            )
    return insights


def _total_insight(expense, target, history) -> Insight | None:
    current = expense[target]
    average = sum(expense[p] for p in history) / len(history)
    change = (current - average) / average
    if abs(change) < TOTAL_CHANGE:
        return None
    more = change > 0
    return Insight(
        "total",
        "warning" if more else "positive",
        "En total gastaste {}% "
        + ("más" if more else "menos")
        + " que tu promedio de {} ({} contra {}).",
        (_percent(current, average), _months(len(history)), current, average),
    )


def _best_month_insight(expense, income, target, year_periods) -> Insight | None:
    active = [p for p in year_periods if expense[p] > 0 or income[p] > 0]
    if len(active) < MIN_HISTORY or target not in active:
        return None
    kept = {p: income[p] - expense[p] for p in active}
    best = kept[target]
    if best <= 0 or any(kept[p] >= best for p in active if p != target):
        return None
    return Insight(
        "best_month",
        "positive",
        "Fue tu mejor mes de ahorro del año: ingresaste {} más de lo que gastaste.",
        (best,),
    )


def build_monthly_insights(user, month: int, year: int, today: date) -> MonthlyInsights | None:
    start_day = getattr(user, "financial_month_start_day", 1)
    target_month, target_year = last_closed_period(month, year, start_day, today)

    # Los 6 períodos anteriores para los promedios y, para "mejor mes del año", todos
    # los del año del período resumido.
    keys = [(target_year, target_month)]
    m, y = target_month, target_year
    while True:
        m, y = _step_back(m, y)
        if len(keys) > WINDOW and y != target_year:
            break
        keys.append((y, m))
    target = keys[0]
    periods = {key: get_financial_period(key[1], key[0], start_day) for key in keys}
    range_start = min(start for start, _ in periods.values())
    range_end = periods[target][1]

    def sums(field):
        return {
            f"p{i}": Sum(field, filter=Q(date__gte=start, date__lt=end), default=Decimal("0"))
            for i, (start, end) in enumerate(periods.values())
        }

    expense_qs = Expense.objects.filter(user=user, date__gte=range_start, date__lt=range_end)
    category_rows = expense_qs.values(
        "category_id", "category__name", "category__parent__name"
    ).annotate(**sums("amount_ars"))
    income_totals = Income.objects.filter(
        user=user, date__gte=range_start, date__lt=range_end
    ).aggregate(**sums("amount_ars"))

    rows = [
        {
            "name": row["category__name"],
            "group": row["category__parent__name"],
            "totals": {key: row[f"p{i}"] for i, key in enumerate(keys)},
        }
        for row in category_rows
    ]
    expense = {key: sum(row["totals"][key] for row in rows) for key in keys}
    income = {key: income_totals[f"p{i}"] for i, key in enumerate(keys)}

    total = expense[target]
    history = [key for key in keys[1 : WINDOW + 1] if expense[key] > 0]
    if total <= 0 or len(history) < MIN_HISTORY:
        return None

    items = sorted(
        _category_insights(rows, target, history, total),
        key=lambda insight: insight.score,
        reverse=True,
    )
    # El total va después de las subcategorías: suele ser la consecuencia de ellas.
    total_insight = _total_insight(expense, target, history)
    if total_insight:
        items.append(total_insight)
    best = _best_month_insight(
        expense, income, target, [key for key in keys if key[0] == target_year]
    )
    if best:
        items.insert(0, best)
    if not items:
        return None
    return MonthlyInsights(month=target_month, year=target_year, items=items[:MAX_INSIGHTS])
