"""
Funciones de utilidad para todo el proyecto
"""

from datetime import date
from decimal import Decimal

from django.utils import timezone


def get_current_month_year():
    """Retorna el mes y año actuales como tupla (month, year)."""
    today = timezone.now().date()
    return today.month, today.year


def get_month_date_range(month: int, year: int):
    """Retorna el rango de fechas para un mes específico

    Args:
        month (int): Número del mes (1-12)
        year (int): Año

    Returns:
        Tupla (fecha_inicio, fecha_fin)
    """

    from calendar import monthrange

    start_date = date(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = date(year, month, last_day)

    return start_date, end_date


def calculate_percentage(partial: Decimal, total: Decimal) -> Decimal:
    """Calcula el porcentaje de un valor parciual sobre un total

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
    """Formatea un monto cohn el símbolo de moneda correspondiente.

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
    current_year = timezone.now().year
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
