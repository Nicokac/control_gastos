"""Tests para la detección de tipo de gasto en la importación de resúmenes PDF."""

from decimal import Decimal

from apps.expenses.importers import ImportedRow


def _row(description, **overrides):
    defaults = {
        "raw_date": "05.07.26",
        "description": description,
        "amount": Decimal("100.00"),
        "currency": "ARS",
    }
    defaults.update(overrides)
    return ImportedRow(**defaults)


class TestInstallmentMatch:
    def test_detects_installment_pattern(self):
        row = _row("DEPILIFE LOMAS DE ZAMORA Cuota 03/06")
        assert row.installment_match == (3, 6)

    def test_no_match_without_pattern(self):
        row = _row("NETFLIX.COM")
        assert row.installment_match is None

    def test_case_insensitive(self):
        row = _row("ALGUN COMERCIO cuota 01/12")
        assert row.installment_match == (1, 12)


class TestSuggestedType:
    def test_installment_takes_priority(self):
        row = _row("NETFLIX.COM Cuota 01/03")
        assert row.suggested_type == "installment"

    def test_known_service_suggests_fixed(self):
        row = _row("NETFLIX.COM")
        assert row.suggested_type == "fixed"

    def test_unknown_merchant_suggests_punctual(self):
        row = _row("ALMACEN DON JOSE")
        assert row.suggested_type == "punctual"

    def test_known_service_substring_match(self):
        row = _row("MERPAGO*SPOTIFY")
        assert row.suggested_type == "fixed"
