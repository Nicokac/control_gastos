"""
Tests para las constantes del sistema.
"""

import pytest
from apps.core.constants import (
    Currency,
    CategoryType,
    PaymentMethod,
    ExpenseType,
    BudgetType,
    DEFAULT_CURRENCY,
    DEFAULT_ALERT_THRESHOLD,
    DEFAULT_EXCHANGE_RATE,
    SYSTEM_CATEGORIES,
)


class TestCurrency:
    """Tests para la clase Currency."""

    def test_currency_choices_exist(self):
        """Verifica que existan las opciones de moneda."""
        choices = Currency.choices
        assert len(choices) == 2

    def test_ars_currency_exists(self):
        """Verifica que exista la moneda ARS."""
        assert Currency.ARS == 'ARS'

    def test_usd_currency_exists(self):
        """Verifica que exista la moneda USD."""
        assert Currency.USD == 'USD'

    def test_ars_label(self):
        """Verifica la etiqueta de ARS."""
        assert Currency.ARS.label == 'Peso Argentino'

    def test_usd_label(self):
        """Verifica la etiqueta de USD."""
        assert Currency.USD.label == 'Dólar Estadounidense'

    def test_currencies_are_different(self):
        """Verifica que las monedas sean diferentes."""
        assert Currency.ARS != Currency.USD


class TestCategoryType:
    """Tests para la clase CategoryType."""

    def test_category_type_choices_exist(self):
        """Verifica que existan las opciones de tipo."""
        choices = CategoryType.choices
        assert len(choices) == 2

    def test_expense_type_exists(self):
        """Verifica que exista el tipo EXPENSE."""
        assert CategoryType.EXPENSE == 'EXPENSE'

    def test_income_type_exists(self):
        """Verifica que exista el tipo INCOME."""
        assert CategoryType.INCOME == 'INCOME'

    def test_expense_label(self):
        """Verifica la etiqueta de EXPENSE."""
        assert CategoryType.EXPENSE.label == 'Gasto'

    def test_income_label(self):
        """Verifica la etiqueta de INCOME."""
        assert CategoryType.INCOME.label == 'Ingreso'

    def test_category_types_are_different(self):
        """Verifica que los tipos sean diferentes."""
        assert CategoryType.EXPENSE != CategoryType.INCOME


class TestPaymentMethod:
    """Tests para la clase PaymentMethod."""

    def test_payment_method_choices_exist(self):
        """Verifica que existan las opciones de método de pago."""
        choices = PaymentMethod.choices
        assert len(choices) == 4

    def test_cash_exists(self):
        """Verifica que exista efectivo."""
        assert PaymentMethod.CASH == 'CASH'

    def test_debit_exists(self):
        """Verifica que exista tarjeta de débito."""
        assert PaymentMethod.DEBIT == 'DEBIT'

    def test_credit_exists(self):
        """Verifica que exista tarjeta de crédito."""
        assert PaymentMethod.CREDIT == 'CREDIT'

    def test_transfer_exists(self):
        """Verifica que exista transferencia."""
        assert PaymentMethod.TRANSFER == 'TRANSFER'

    def test_cash_label(self):
        """Verifica la etiqueta de efectivo."""
        assert PaymentMethod.CASH.label == 'Efectivo'

    def test_debit_label(self):
        """Verifica la etiqueta de débito."""
        assert PaymentMethod.DEBIT.label == 'Tarjeta de Débito'

    def test_credit_label(self):
        """Verifica la etiqueta de crédito."""
        assert PaymentMethod.CREDIT.label == 'Tarjeta de Crédito'

    def test_transfer_label(self):
        """Verifica la etiqueta de transferencia."""
        assert PaymentMethod.TRANSFER.label == 'Transferencia'


class TestExpenseType:
    """Tests para la clase ExpenseType."""

    def test_expense_type_choices_exist(self):
        """Verifica que existan las opciones de tipo de gasto."""
        choices = ExpenseType.choices
        assert len(choices) == 2

    def test_fixed_exists(self):
        """Verifica que exista tipo fijo."""
        assert ExpenseType.FIXED == 'FIXED'

    def test_variable_exists(self):
        """Verifica que exista tipo variable."""
        assert ExpenseType.VARIABLE == 'VARIABLE'

    def test_fixed_label(self):
        """Verifica la etiqueta de fijo."""
        assert ExpenseType.FIXED.label == 'Fijo'

    def test_variable_label(self):
        """Verifica la etiqueta de variable."""
        assert ExpenseType.VARIABLE.label == 'Variable'

    def test_expense_types_are_different(self):
        """Verifica que los tipos sean diferentes."""
        assert ExpenseType.FIXED != ExpenseType.VARIABLE


class TestBudgetType:
    """Tests para la clase BudgetType."""

    def test_budget_type_choices_exist(self):
        """Verifica que existan las opciones de tipo de presupuesto."""
        choices = BudgetType.choices
        assert len(choices) == 2

    def test_global_exists(self):
        """Verifica que exista tipo global."""
        assert BudgetType.GLOBAL == 'GLOBAL'

    def test_by_category_exists(self):
        """Verifica que exista tipo por categoría."""
        assert BudgetType.BY_CATEGORY == 'BY_CATEGORY'

    def test_global_label(self):
        """Verifica la etiqueta de global."""
        assert BudgetType.GLOBAL.label == 'Global Mensual'

    def test_by_category_label(self):
        """Verifica la etiqueta de por categoría."""
        assert BudgetType.BY_CATEGORY.label == 'Por Categoría'


class TestDefaultValues:
    """Tests para los valores por defecto."""

    def test_default_currency_is_ars(self):
        """Verifica que la moneda por defecto sea ARS."""
        assert DEFAULT_CURRENCY == Currency.ARS

    def test_default_alert_threshold(self):
        """Verifica el umbral de alerta por defecto."""
        assert DEFAULT_ALERT_THRESHOLD == 80
        assert isinstance(DEFAULT_ALERT_THRESHOLD, int)

    def test_default_exchange_rate(self):
        """Verifica el tipo de cambio por defecto."""
        assert DEFAULT_EXCHANGE_RATE == 1.0000
        assert isinstance(DEFAULT_EXCHANGE_RATE, float)


class TestSystemCategories:
    """Tests para las categorías del sistema."""

    def test_system_categories_has_expense_and_income(self):
        """Verifica que existan categorías de gasto e ingreso."""
        assert 'EXPENSE' in SYSTEM_CATEGORIES
        assert 'INCOME' in SYSTEM_CATEGORIES

    def test_expense_categories_not_empty(self):
        """Verifica que haya categorías de gasto."""
        assert len(SYSTEM_CATEGORIES['EXPENSE']) > 0

    def test_income_categories_not_empty(self):
        """Verifica que haya categorías de ingreso."""
        assert len(SYSTEM_CATEGORIES['INCOME']) > 0

    def test_expense_categories_have_required_fields(self):
        """Verifica que las categorías de gasto tengan los campos requeridos."""
        for category in SYSTEM_CATEGORIES['EXPENSE']:
            assert 'name' in category
            assert 'icon' in category
            assert 'color' in category

    def test_income_categories_have_required_fields(self):
        """Verifica que las categorías de ingreso tengan los campos requeridos."""
        for category in SYSTEM_CATEGORIES['INCOME']:
            assert 'name' in category
            assert 'icon' in category
            assert 'color' in category

    def test_expense_categories_icons_start_with_bi(self):
        """Verifica que los iconos de gasto sean de Bootstrap Icons."""
        for category in SYSTEM_CATEGORIES['EXPENSE']:
            assert category['icon'].startswith('bi-')

    def test_income_categories_icons_start_with_bi(self):
        """Verifica que los iconos de ingreso sean de Bootstrap Icons."""
        for category in SYSTEM_CATEGORIES['INCOME']:
            assert category['icon'].startswith('bi-')

    def test_expense_categories_colors_are_hex(self):
        """Verifica que los colores de gasto sean hexadecimales."""
        for category in SYSTEM_CATEGORIES['EXPENSE']:
            assert category['color'].startswith('#')
            assert len(category['color']) == 7

    def test_income_categories_colors_are_hex(self):
        """Verifica que los colores de ingreso sean hexadecimales."""
        for category in SYSTEM_CATEGORIES['INCOME']:
            assert category['color'].startswith('#')
            assert len(category['color']) == 7

    def test_alimentacion_exists_in_expenses(self):
        """Verifica que exista la categoría Alimentación."""
        names = [c['name'] for c in SYSTEM_CATEGORIES['EXPENSE']]
        assert 'Alimentación' in names

    def test_sueldo_exists_in_income(self):
        """Verifica que exista la categoría Sueldo."""
        names = [c['name'] for c in SYSTEM_CATEGORIES['INCOME']]
        assert 'Sueldo' in names