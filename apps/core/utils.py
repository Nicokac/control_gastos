"""
Funciones de utilidad para todo el proyecto
"""

import logging
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

import requests

logger = logging.getLogger(__name__)


def send_brevo_email(to_email: str, subject: str, body: str) -> bool:
    """Envía un email via Brevo API HTTP. Retorna True si tuvo éxito."""
    brevo_api_key = getattr(settings, "BREVO_API_KEY", "")
    if not brevo_api_key:
        return False
    try:
        requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": brevo_api_key, "Content-Type": "application/json"},
            json={
                "sender": {"name": "Control Gastos", "email": "kachuknm@gmail.com"},
                "to": [{"email": to_email}],
                "subject": subject,
                "textContent": body,
            },
            timeout=10,
        ).raise_for_status()
        return True
    except Exception:
        logger.exception("Error al enviar email via Brevo a %s", to_email)
        return False


def get_current_month_year():
    """Retorna el mes y año actuales como tupla (month, year)."""
    today = timezone.localdate()
    return today.month, today.year


def calculate_percentage(partial: Decimal, total: Decimal) -> Decimal:
    """Calcula el porcentaje de un valor parcial sobre un total

    Args:
        partial (Decimal): Valor parcial
        total (Decimal): Valor total

    Returns:
        Porcentaje como Decimal (0-100)
    """
    if total == 0:
        return Decimal("0")
    return (partial / total) * 100


def format_currency(amount: Decimal, currency: str = "ARS") -> str:
    """Formatea un monto con el símbolo de moneda correspondiente.

    Args:
        amount (Decimal): Monto a formatear
        currency (str, optional): Código de moneda ('ARS' o 'USD'). Defaults to 'ARS'.

    Returns:
        String formateado (ej: "$ 1.234,56" o "US$ 100.00")
    """
    symbol = "$" if currency == "ARS" else "US$"
    formatted = f"{abs(amount):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "-" if amount < 0 else ""
    return f"{sign}{symbol} {formatted}"


def get_month_name(month: int) -> str:
    """Retorna el nombre del mes en español.

    Args:
        month (int): Número del mes (1-12)

    Returns:
        String: Nombre del mes
    """
    months = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    return months.get(month, "")


def get_years_choices(start_year: int = 2020):
    """Genera una lista de años para usar en formularios.

    Args:
        start_year (int, optional): Año inicial. Defaults to 2020.

    Returns:
        Lista de tuplas (year, year) para choices
    """
    current_year = timezone.localdate().year
    return [(year, str(year)) for year in range(start_year, current_year + 2)]


def get_months_choices():
    """Genera una lista de meses para usar en formularios.

    Returns:
        Lista de tuplas (month_number, month_name) para choices
    """
    return [(i, get_month_name(i)) for i in range(1, 13)]


def get_month_date_range_exclusive(month: int, year: int):
    """Retorna (inicio, fin_exclusivo) para queries: [inicio, fin_exclusivo)."""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return start_date, end_date


def get_financial_period(month: int, year: int, start_day: int = 1):
    """
    Retorna (inicio, fin_exclusivo) del período financiero del usuario.

    Si start_day == 1, equivale a get_month_date_range_exclusive (mes calendario).
    Si start_day > 1, el período va del día start_day del mes seleccionado
    al día start_day del mes siguiente.

    Ejemplo: month=5, year=2026, start_day=10
    → inicio: 2026-05-10, fin: 2026-06-10

    El navegador selecciona el mes "Mayo" y el período real es 10/05 al 09/06.
    """
    import calendar as cal_module

    if start_day <= 1:
        return get_month_date_range_exclusive(month, year)

    # Inicio: día start_day del mes seleccionado (clamp al último día del mes)
    last_day = cal_module.monthrange(year, month)[1]
    actual_start_day = min(start_day, last_day)
    start_date = date(year, month, actual_start_day)

    # Fin: día start_day del mes siguiente
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    last_day_next = cal_module.monthrange(next_year, next_month)[1]
    actual_end_day = min(start_day, last_day_next)
    end_date = date(next_year, next_month, actual_end_day)

    return start_date, end_date


def get_next_month_commitment(user, next_month: int, next_year: int) -> dict:
    """
    Estima cuánto del mes siguiente ya está comprometido: gastos fijos
    activos (incluye cuotas en curso) vs. ingresos fijos esperados.

    El monto de cada recurrente se infiere de su último pago/cobro
    registrado. Los que nunca se pagaron no tienen monto estimable y
    se listan aparte para no subestimar el total con $0.
    """
    from apps.recurring.models import RecurringExpense
    from apps.recurring_income.models import RecurringIncome

    expense_recurrents = RecurringExpense.objects.filter(
        user=user, is_active=True
    ).prefetch_related("expenses")
    income_recurrents = RecurringIncome.objects.filter(user=user, is_active=True).prefetch_related(
        "incomes"
    )

    committed_items = []
    committed_total = Decimal("0")
    committed_unestimated = []
    for r in expense_recurrents:
        last = r.last_expense
        if last is None:
            committed_unestimated.append(r)
            continue
        committed_items.append({"rec": r, "amount": last.amount_ars})
        committed_total += last.amount_ars

    expected_items = []
    expected_total = Decimal("0")
    expected_unestimated = []
    for r in income_recurrents:
        last = r.last_income
        if last is None:
            expected_unestimated.append(r)
            continue
        expected_items.append({"rec": r, "amount": last.amount_ars})
        expected_total += last.amount_ars

    return {
        "next_month_name": get_month_name(next_month),
        "next_month_committed_total": committed_total,
        "next_month_committed_items": committed_items,
        "next_month_committed_unestimated": committed_unestimated,
        "next_month_expected_total": expected_total,
        "next_month_expected_items": expected_items,
        "next_month_expected_unestimated": expected_unestimated,
        "next_month_free_balance": expected_total - committed_total,
        "next_month_commitment_available": bool(committed_items or expected_items),
    }
