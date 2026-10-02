"""Tests para los filtros de template de moneda."""

from decimal import Decimal

from apps.core.templatetags.currency_filters import currency, sensitive_currency


class TestSensitiveCurrency:
    """Tests para el filtro sensitive_currency (DT-065 — botón de ojo del dashboard)."""

    def test_wraps_value_in_sensitive_amount_span(self):
        result = sensitive_currency(Decimal("1500.00"))
        assert result == '<span class="sensitive-amount">$ 1.500,00</span>'

    def test_matches_currency_filter_formatting(self):
        value = Decimal("2345.67")
        assert currency(value) in sensitive_currency(value)

    def test_handles_none_like_currency(self):
        assert sensitive_currency(None) == '<span class="sensitive-amount">$ 0,00</span>'

    def test_is_marked_safe(self):
        result = sensitive_currency(Decimal("100.00"))
        assert hasattr(result, "__html__")
