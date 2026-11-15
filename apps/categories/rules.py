"""Reglas de categorización: "si la descripción contiene estas palabras, va a esta categoría"."""

import re
import unicodedata

from .models import Category, CategoryRule

MAX_PATTERN_LENGTH = 100


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def get_active_rules(user) -> list[CategoryRule]:
    """Reglas cuya categoría sigue disponible, de la más específica a la más general."""
    rules = CategoryRule.objects.filter(
        user=user, category__in=Category.get_expense_categories(user)
    ).select_related("category")
    return sorted(rules, key=lambda r: (-len(r.pattern.split()), -len(r.pattern), r.pattern))


def match_rule(rules: list[CategoryRule], text: str) -> CategoryRule | None:
    haystack = f" {normalize_text(text)} "
    return next((r for r in rules if f" {r.pattern} " in haystack), None)


def find_rule(user, text: str) -> CategoryRule | None:
    return match_rule(get_active_rules(user), text)


def learn_rule(user, text: str, category: Category) -> CategoryRule | None:
    """Crea o actualiza la regla con la descripción completa; None si no queda texto."""
    pattern = normalize_text(text)
    if len(pattern) > MAX_PATTERN_LENGTH:
        pattern = pattern[: MAX_PATTERN_LENGTH + 1].rsplit(" ", 1)[0]
    if not pattern:
        return None
    rule, _ = CategoryRule.objects.update_or_create(
        user=user, pattern=pattern, defaults={"category": category}
    )
    return rule
