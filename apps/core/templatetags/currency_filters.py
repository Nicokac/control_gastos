from decimal import Decimal, InvalidOperation

from django import template

from apps.core.utils import format_currency

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
    return format_currency(value, currency_code)
