from decimal import Decimal, InvalidOperation

from django import template
from django.utils.http import urlencode

from apps.core.utils import format_currency

register = template.Library()


@register.simple_tag(takes_context=True)
def sort_url(context, field):
    request = context["request"]
    current_order = request.GET.get("order_by", "date")
    current_dir = request.GET.get("dir", "desc")
    new_dir = "asc" if (current_order == field and current_dir == "desc") else "desc"
    params = {k: v for k, v in request.GET.items() if k not in ("order_by", "dir")}
    params["order_by"] = field
    params["dir"] = new_dir
    return "?" + urlencode(params)


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
