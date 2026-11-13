"""Carga rápida: interpreta una línea como "15000 super débito" y arma un gasto sin guardarlo."""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Count, Q
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import Currency, PaymentMethod
from apps.core.utils import get_official_usd_rate
from apps.expenses.models import Expense

MAX_TEXT_LENGTH = 200
HISTORY_DAYS = 365

PAYMENT_WORDS = {
    "debito": PaymentMethod.DEBIT,
    "deb": PaymentMethod.DEBIT,
    "credito": PaymentMethod.CREDIT,
    "tarjeta": PaymentMethod.CREDIT,
    "tc": PaymentMethod.CREDIT,
    "efectivo": PaymentMethod.CASH,
    "efvo": PaymentMethod.CASH,
    "cash": PaymentMethod.CASH,
    "transferencia": PaymentMethod.TRANSFER,
    "transf": PaymentMethod.TRANSFER,
}
USD_WORDS = {"usd", "u$s", "us$", "u$d", "dolar", "dolares"}
RELATIVE_DAYS = {"hoy": 0, "ayer": 1, "anteayer": 2}
STOPWORDS = {
    "en",
    "el",
    "la",
    "los",
    "las",
    "de",
    "del",
    "con",
    "por",
    "un",
    "una",
    "al",
    "y",
    "pague",
    "gaste",
    "compre",
}

AMOUNT_RE = re.compile(
    r"^(?P<prefix>\$|u\$s|us\$|usd)?"
    r"(?P<number>\d{1,3}(?:\.\d{3})+|\d+)(?:,(?P<decimals>\d{1,2})|\.(?P<dot_decimals>\d{1,2}))?"
    r"(?P<k>k)?$"
)
DATE_RE = re.compile(r"^(?P<day>\d{1,2})/(?P<month>\d{1,2})(?:/(?P<year>\d{2}|\d{4}))?$")


class QuickEntryError(Exception):
    """El texto no alcanza para armar un gasto; el mensaje se muestra al usuario."""


@dataclass
class QuickExpense:
    amount: Decimal
    currency: str
    exchange_rate: Decimal
    date: date
    payment_method: str
    description: str
    category: Category | None
    category_source: str | None


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _parse_amount(token: str) -> tuple[Decimal, bool, bool] | None:
    """(monto, tiene prefijo de moneda, es USD) o None si el token no es un monto."""
    match = AMOUNT_RE.match(token)
    if not match:
        return None
    number = match["number"].replace(".", "")
    decimals = match["decimals"] or match["dot_decimals"]
    try:
        value = Decimal(f"{number}.{decimals}" if decimals else number)
    except InvalidOperation:
        return None
    if match["k"]:
        value *= 1000
    prefix = match["prefix"] or ""
    return value, prefix != "", prefix not in ("", "$")


def _parse_date(token: str, today: date) -> date | None:
    if token in RELATIVE_DAYS:
        return today - timedelta(days=RELATIVE_DAYS[token])
    match = DATE_RE.match(token)
    if not match:
        return None
    year = int(match["year"]) if match["year"] else today.year
    if year < 100:
        year += 2000
    try:
        parsed = date(year, int(match["month"]), int(match["day"]))
    except ValueError:
        return None
    if not match["year"] and parsed > today:
        parsed = parsed.replace(year=year - 1)
    return parsed


def suggest_category(user, words: list[str]) -> tuple[Category | None, str | None]:
    """Categoría más usada en gastos con esas palabras; si no hay historial, la que las nombra."""
    keywords = [w for w in words if len(w) >= 3]
    if not keywords:
        return None, None
    available = Category.get_expense_categories(user)

    since = timezone.localdate() - timedelta(days=HISTORY_DAYS)
    matches = Q()
    for word in keywords:
        matches |= Q(description__icontains=word)
    top = (
        Expense.objects.filter(matches, user=user, date__gte=since, category__in=available)
        .values("category")
        .annotate(uses=Count("id"))
        .order_by("-uses", "category")
        .first()
    )
    if top:
        return available.get(pk=top["category"]), "historial"

    scores = Counter()
    for category in available:
        name = _normalize(category.name)
        for word in keywords:
            if word in name:
                scores[category] += 1
    if scores:
        return scores.most_common(1)[0][0], "nombre"
    return None, None


def parse_quick_expense(user, text: str) -> QuickExpense:
    text = (text or "").strip()
    if not text:
        raise QuickEntryError("Escribí el gasto, por ejemplo: 15000 super débito.")
    if len(text) > MAX_TEXT_LENGTH:
        raise QuickEntryError(f"El texto es muy largo (máximo {MAX_TEXT_LENGTH} caracteres).")

    today = timezone.localdate()
    amounts = []
    currency = Currency.ARS
    expense_date = today
    payment_method = ""
    description_words = []

    for position, raw in enumerate(text.split()):
        token = _normalize(raw).strip(".,;:")
        if token in USD_WORDS:
            currency = Currency.USD
            continue
        if token in PAYMENT_WORDS:
            payment_method = PAYMENT_WORDS[token]
            continue
        parsed_date = _parse_date(token, today)
        if parsed_date:
            expense_date = parsed_date
            continue
        parsed_amount = _parse_amount(token)
        if parsed_amount:
            value, has_prefix, is_usd = parsed_amount
            amounts.append((value, has_prefix, position, raw))
            if is_usd:
                currency = Currency.USD
            continue
        if token in STOPWORDS:
            continue
        description_words.append((position, raw.strip(",;:")))

    if not amounts:
        raise QuickEntryError("No encontré el monto. Probá con algo como: 15000 super débito.")
    # The amount is the one written with "$"; otherwise the largest number, and any
    # other number stays in the description ("netflix 4 pantallas 8000").
    marked = [a for a in amounts if a[1]]
    chosen = marked[0] if marked else max(amounts, key=lambda a: a[0])
    description_words += [(a[2], a[3]) for a in amounts if a is not chosen]
    description_words = [word for _, word in sorted(description_words)]
    amount = chosen[0]
    if amount <= 0:
        raise QuickEntryError("El monto tiene que ser mayor a cero.")

    exchange_rate = Decimal("1")
    if currency == Currency.USD:
        exchange_rate = get_official_usd_rate()
        if exchange_rate is None:
            raise QuickEntryError(
                "No pude obtener la cotización del dólar. Cargá el gasto con el formulario completo."
            )

    description = " ".join(description_words)
    category, source = suggest_category(user, [_normalize(w) for w in description_words])
    return QuickExpense(
        amount=amount,
        currency=currency,
        exchange_rate=exchange_rate,
        date=expense_date,
        payment_method=payment_method,
        description=description,
        category=category,
        category_source=source,
    )


def quick_expense_to_dict(parsed: QuickExpense) -> dict:
    from apps.core.templatetags.currency_filters import currency as format_currency

    return {
        "amount": str(parsed.amount),
        "amount_display": format_currency(parsed.amount, parsed.currency),
        "conversion_display": (
            f"≈ {format_currency(parsed.amount * parsed.exchange_rate)} "
            f"(dólar oficial {format_currency(parsed.exchange_rate)})"
            if parsed.currency == Currency.USD
            else ""
        ),
        "currency": parsed.currency,
        "exchange_rate": str(parsed.exchange_rate),
        "date": parsed.date.isoformat(),
        "date_display": parsed.date.strftime("%d/%m/%Y"),
        "payment_method": parsed.payment_method,
        "payment_method_display": dict(PaymentMethod.choices).get(parsed.payment_method, ""),
        "description": parsed.description,
        "category_id": parsed.category.pk if parsed.category else None,
        "category_name": parsed.category.name if parsed.category else None,
        "category_source": parsed.category_source,
    }
