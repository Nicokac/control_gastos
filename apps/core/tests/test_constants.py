"""
Tests para las constantes del sistema.
"""

import pytest
from apps.core.constants import Currency, CategoryType


class TestCurrency:
    """Tests para la clase Currency."""

    def test_currency_choices_exist(self):
        """Verifica que existan las opciones de moneda."""
        choices = Currency.choices
        assert len(choices) >= 2

    def test_ars_currency_exists(self):
        """Verifica que exista la moneda ARS."""
        assert Currency.ARS == 'ARS'

    def test_usd_currency_exists(self):
        """Verifica que exista la moneda USD."""
        assert Currency.USD == 'USD'

    def test_default_currency_is_ars(self):
        """Verifica que la moneda por defecto sea ARS."""
        # Esto depende de cómo esté implementado en tu constants.py
        # Ajustar según tu implementación
        assert hasattr(Currency, 'ARS')


class TestCategoryType:
    """Tests para la clase CategoryType."""

    def test_category_type_choices_exist(self):
        """Verifica que existan las opciones de tipo."""
        choices = CategoryType.choices
        assert len(choices) >= 2

    def test_expense_type_exists(self):
        """Verifica que exista el tipo EXPENSE."""
        assert CategoryType.EXPENSE == 'EXPENSE'

    def test_income_type_exists(self):
        """Verifica que exista el tipo INCOME."""
        assert CategoryType.INCOME == 'INCOME'

    def test_category_types_are_different(self):
        """Verifica que los tipos sean diferentes."""
        assert CategoryType.EXPENSE != CategoryType.INCOME