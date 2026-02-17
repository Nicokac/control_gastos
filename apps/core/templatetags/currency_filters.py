from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="currency")
def currency(value, currency_code="ARS"):
    if value is None or value == "":
        return "$ 0,00"
    try:
        if isinstance(value, str):
            value = Decimal(value)
        elif isinstance(value, (int, float)):
            value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return "$ 0,00"

    symbol = "$" if currency_code == "ARS" else "US$"
    formatted = f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sign = "-" if value < 0 else ""
    return f"{sign}{symbol} {formatted}"
