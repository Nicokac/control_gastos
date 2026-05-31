"""
Tests para las funciones de utilidad.
"""

from decimal import Decimal

from django.utils import timezone

from apps.core.utils import (
    calculate_percentage,
    format_currency,
    get_current_month_year,
    get_financial_period,
    get_month_date_range_exclusive,
    get_month_name,
    get_months_choices,
    get_years_choices,
    send_brevo_email,
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


class TestGetMonthDateRangeExclusive:
    def test_normal_month(self):
        start, end = get_month_date_range_exclusive(5, 2026)
        from datetime import date

        assert start == date(2026, 5, 1)
        assert end == date(2026, 6, 1)

    def test_december_wraps_to_next_year(self):
        start, end = get_month_date_range_exclusive(12, 2026)
        from datetime import date

        assert start == date(2026, 12, 1)
        assert end == date(2027, 1, 1)

    def test_january(self):
        start, end = get_month_date_range_exclusive(1, 2026)
        from datetime import date

        assert start == date(2026, 1, 1)
        assert end == date(2026, 2, 1)


class TestGetFinancialPeriod:
    def test_start_day_1_equals_calendar_month(self):
        from datetime import date

        start, end = get_financial_period(5, 2026, start_day=1)
        assert start == date(2026, 5, 1)
        assert end == date(2026, 6, 1)

    def test_start_day_0_equals_calendar_month(self):
        from datetime import date

        start, end = get_financial_period(5, 2026, start_day=0)
        assert start == date(2026, 5, 1)
        assert end == date(2026, 6, 1)

    def test_custom_start_day(self):
        from datetime import date

        start, end = get_financial_period(5, 2026, start_day=10)
        assert start == date(2026, 5, 10)
        assert end == date(2026, 6, 10)

    def test_december_with_custom_start_day(self):
        from datetime import date

        start, end = get_financial_period(12, 2026, start_day=15)
        assert start == date(2026, 12, 15)
        assert end == date(2027, 1, 15)

    def test_start_day_clamps_to_last_day_of_month(self):
        from datetime import date

        # Febrero 2026 tiene 28 días, start_day=31 debe clampearse a 28
        start, end = get_financial_period(2, 2026, start_day=31)
        assert start == date(2026, 2, 28)

    def test_end_day_clamps_to_last_day_of_next_month(self):
        from datetime import date

        # start_day=31 en enero → fin en febrero (28 días en 2026)
        start, end = get_financial_period(1, 2026, start_day=31)
        assert end == date(2026, 2, 28)


class TestSendBrevoEmail:
    def test_returns_false_without_api_key(self, settings):
        settings.BREVO_API_KEY = ""
        result = send_brevo_email("test@example.com", "Asunto", "Cuerpo")
        assert result is False

    def test_returns_true_on_success(self, settings):
        from unittest.mock import MagicMock, patch

        settings.BREVO_API_KEY = "fake-key"  # pragma: allowlist secret
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch("apps.core.utils.requests.post", return_value=mock_response) as mock_post:
            result = send_brevo_email("dest@example.com", "Asunto", "Cuerpo")

        assert result is True
        mock_post.assert_called_once()

    def test_returns_false_on_exception(self, settings):
        from unittest.mock import patch

        import requests as req

        settings.BREVO_API_KEY = "fake-key"  # pragma: allowlist secret

        with patch("apps.core.utils.requests.post", side_effect=req.exceptions.ConnectionError):
            result = send_brevo_email("dest@example.com", "Asunto", "Cuerpo")

        assert result is False

    def test_sends_to_correct_email(self, settings):
        from unittest.mock import MagicMock, patch

        settings.BREVO_API_KEY = "fake-key"  # pragma: allowlist secret
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch("apps.core.utils.requests.post", return_value=mock_response) as mock_post:
            send_brevo_email("destino@test.com", "Asunto", "Cuerpo")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["to"][0]["email"] == "destino@test.com"
