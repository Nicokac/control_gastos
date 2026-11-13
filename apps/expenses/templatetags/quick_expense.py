from django import template

from apps.categories.models import Category
from apps.core.constants import CategoryType

register = template.Library()


@register.inclusion_tag("expenses/_quick_expense.html", takes_context=True)
def quick_expense_bar(context):
    request = context["request"]
    return {
        "category_groups": Category.get_categories_by_group(request.user, CategoryType.EXPENSE),
        "next_url": request.get_full_path(),
        "csrf_token": context.get("csrf_token"),
        "APP_VERSION": context.get("APP_VERSION"),
    }
