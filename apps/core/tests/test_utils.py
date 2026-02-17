"""
Tests para las funciones de utilidad.
"""

from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.core.utils import (
    calculate_percentage,
    format_currency,
    get_current_month_year,
    get_month_date_range,
    get_month_name,
    get_months_choices,
    get_years_choices,
)


class TestGetCurrentMonthYear:
    """Tests para get_current_month_year()."""

    def test_returns_tuple(self):
        """Verifica que retorne una tupla."""
        result = get_current_month_year()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_current_month(self):
        """Verifica que retorne el mes actual."""
        month, year = get_current_month_year()
        today = timezone.now().date()
        assert month == today.month
        assert year == today.year

    def test_month_in_valid_range(self):
        """Verifica que el mes esté en rango válido."""
        month, _ = get_current_month_year()
        assert 1 <= month <= 12

    def test_year_is_reasonable(self):
        """Verifica que el año sea razonable."""
        _, year = get_current_month_year()
        assert 2020 <= year <= 2100


class TestGetMonthDateRange:
    """Tests para get_month_date_range()."""

    def test_january_range(self):
        """Verifica el rango de enero."""
        start, end = get_month_date_range(1, 2025)
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)

    def test_february_non_leap_year(self):
        """Verifica febrero en año no bisiesto."""
        start, end = get_month_date_range(2, 2025)
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_february_leap_year(self):
        """Verifica febrero en año bisiesto."""
        start, end = get_month_date_range(2, 2024)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_december_range(self):
        """Verifica el rango de diciembre."""
        start, end = get_month_date_range(12, 2025)
        assert start == date(2025, 12, 1)
        assert end == date(2025, 12, 31)

    def test_april_30_days(self):
        """Verifica un mes de 30 días."""
        start, end = get_month_date_range(4, 2025)
        assert start == date(2025, 4, 1)
        assert end == date(2025, 4, 30)


class TestCalculatePercentage:
    """Tests para calculate_percentage()."""

    def test_basic_percentage(self):
        """Verifica cálculo básico de porcentaje."""
        result = calculate_percentage(Decimal("25"), Decimal("100"))
        assert result == Decimal("25")

    def test_fifty_percent(self):
        """Verifica 50%."""
        result = calculate_percentage(Decimal("50"), Decimal("100"))
        assert result == Decimal("50")

    def test_hundred_percent(self):
        """Verifica 100%."""
        result = calculate_percentage(Decimal("100"), Decimal("100"))
        assert result == Decimal("100")

    def test_zero_partial(self):
        """Verifica con parcial en cero."""
        result = calculate_percentage(Decimal("0"), Decimal("100"))
        assert result == Decimal("0")

    def test_zero_total_returns_zero(self):
        """Verifica que total cero retorne cero (evita división por cero)."""
        result = calculate_percentage(Decimal("50"), Decimal("0"))
        assert result == Decimal("0")

    def test_over_hundred_percent(self):
        """Verifica porcentaje mayor a 100."""
        result = calculate_percentage(Decimal("150"), Decimal("100"))
        assert result == Decimal("150")

    def test_decimal_precision(self):
        """Verifica precisión decimal."""
        result = calculate_percentage(Decimal("1"), Decimal("3"))
        # 1/3 * 100 = 33.333...
        assert result > Decimal("33")
        assert result < Decimal("34")


class TestFormatCurrency:
    """Tests para format_currency()."""

    def test_format_ars_default(self):
        result = format_currency(Decimal("1500.50"))
        assert result == "$ 1.500,50"

    def test_format_large_number(self):
        result = format_currency(Decimal("996253.11"))
        assert result == "$ 996.253,11"

    def test_format_ars_explicit(self):
        """Verifica formato ARS explícito."""
        result = format_currency(Decimal("1500.50"), "ARS")
        assert "$" in result

    def test_format_usd(self):
        """Verifica formato USD."""
        result = format_currency(Decimal("100.00"), "USD")
        assert "US$" in result

    def test_format_zero(self):
        """Verifica formato de cero."""
        result = format_currency(Decimal("0"))
        assert "0" in result

    def test_format_negative(self):
        """Verifica formato de número negativo."""
        result = format_currency(Decimal("-500.00"))
        assert "-" in result or "500" in result


class TestGetMonthName:
    """Tests para get_month_name()."""

    def test_january(self):
        """Verifica nombre de enero."""
        assert get_month_name(1) == "Enero"

    def test_february(self):
        """Verifica nombre de febrero."""
        assert get_month_name(2) == "Febrero"

    def test_december(self):
        """Verifica nombre de diciembre."""
        assert get_month_name(12) == "Diciembre"

    def test_all_months_exist(self):
        """Verifica que todos los meses tengan nombre."""
        for month in range(1, 13):
            name = get_month_name(month)
            assert name != ""
            assert len(name) > 0

    def test_invalid_month_returns_empty(self):
        """Verifica que mes inválido retorne vacío."""
        assert get_month_name(0) == ""
        assert get_month_name(13) == ""
        assert get_month_name(-1) == ""


class TestGetYearsChoices:
    """Tests para get_years_choices()."""

    def test_returns_list(self):
        """Verifica que retorne una lista."""
        result = get_years_choices()
        assert isinstance(result, list)

    def test_contains_current_year(self):
        """Verifica que contenga el año actual."""
        current_year = timezone.now().year
        years = [y[0] for y in get_years_choices()]
        assert current_year in years

    def test_contains_tuples(self):
        """Verifica que contenga tuplas."""
        result = get_years_choices()
        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)

    def test_starts_from_2020_by_default(self):
        """Verifica que empiece desde 2020 por defecto."""
        years = [y[0] for y in get_years_choices()]
        assert 2020 in years

    def test_custom_start_year(self):
        """Verifica año de inicio personalizado."""
        years = [y[0] for y in get_years_choices(start_year=2023)]
        assert 2023 in years
        assert 2020 not in years


class TestGetMonthsChoices:
    """Tests para get_months_choices()."""

    def test_returns_12_months(self):
        """Verifica que retorne 12 meses."""
        result = get_months_choices()
        assert len(result) == 12

    def test_returns_list_of_tuples(self):
        """Verifica que retorne lista de tuplas."""
        result = get_months_choices()
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) for item in result)

    def test_first_month_is_january(self):
        """Verifica que el primer mes sea enero."""
        result = get_months_choices()
        assert result[0][0] == 1
        assert result[0][1] == "Enero"

    def test_last_month_is_december(self):
        """Verifica que el último mes sea diciembre."""
        result = get_months_choices()
        assert result[11][0] == 12
        assert result[11][1] == "Diciembre"

    def test_months_are_in_order(self):
        """Verifica que los meses estén en orden."""
        result = get_months_choices()
        month_numbers = [item[0] for item in result]
        assert month_numbers == list(range(1, 13))
