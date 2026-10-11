"""
Tests para los servicios de traslado de sobrante (DT-067).
"""

from datetime import date
from decimal import Decimal

import pytest

from apps.savings.models import RolloverSuggestion, RolloverSuggestionStatus, SavingMovement
from apps.savings.services import (
    confirm_rollover_deposit,
    get_dismissed_amount_for_current_period,
    get_or_create_rollover_income_category,
    get_or_create_rollover_suggestion,
    get_period_balance,
    get_previous_period,
)


@pytest.mark.django_db
class TestGetPeriodBalance:
    """Tests para get_period_balance."""

    def test_balance_positivo(
        self, user, expense_category, income_category, expense_factory, income_factory
    ):
        income_factory(user, income_category, amount=Decimal("1000.00"), date=date(2026, 1, 15))
        expense_factory(user, expense_category, amount=Decimal("300.00"), date=date(2026, 1, 20))

        balance = get_period_balance(user, date(2026, 1, 1), date(2026, 2, 1))

        assert balance == Decimal("700.00")

    def test_balance_resta_depositos_de_ahorro(
        self, user, income_category, income_factory, saving_factory, saving_movement_factory
    ):
        income_factory(user, income_category, amount=Decimal("1000.00"), date=date(2026, 1, 15))
        saving = saving_factory(user)
        movement = saving_movement_factory(
            saving, movement_type="DEPOSIT", amount=Decimal("200.00")
        )
        SavingMovement.objects.filter(pk=movement.pk).update(date=date(2026, 1, 20))

        balance = get_period_balance(user, date(2026, 1, 1), date(2026, 2, 1))

        assert balance == Decimal("800.00")

    def test_balance_cero_sin_movimientos(self, user):
        balance = get_period_balance(user, date(2026, 1, 1), date(2026, 2, 1))

        assert balance == Decimal("0")

    def test_balance_negativo(self, user, expense_category, expense_factory):
        expense_factory(user, expense_category, amount=Decimal("500.00"), date=date(2026, 1, 10))

        balance = get_period_balance(user, date(2026, 1, 1), date(2026, 2, 1))

        assert balance == Decimal("-500.00")

    def test_excluye_movimientos_fuera_de_rango(
        self, user, expense_category, income_category, expense_factory, income_factory
    ):
        income_factory(user, income_category, amount=Decimal("1000.00"), date=date(2025, 12, 31))
        expense_factory(user, expense_category, amount=Decimal("1000.00"), date=date(2026, 2, 1))

        balance = get_period_balance(user, date(2026, 1, 1), date(2026, 2, 1))

        assert balance == Decimal("0")


class TestGetPreviousPeriod:
    """Tests para get_previous_period."""

    def test_mes_calendario_normal(self):
        start, end = get_previous_period(month=3, year=2026, start_day=1)

        assert start == date(2026, 2, 1)
        assert end == date(2026, 3, 1)

    def test_cruza_de_enero_a_diciembre_del_anio_anterior(self):
        start, end = get_previous_period(month=1, year=2026, start_day=1)

        assert start == date(2025, 12, 1)
        assert end == date(2026, 1, 1)

    def test_periodo_financiero_con_start_day(self):
        start, end = get_previous_period(month=5, year=2026, start_day=10)

        assert start == date(2026, 4, 10)
        assert end == date(2026, 5, 10)


@pytest.mark.django_db
class TestGetOrCreateRolloverSuggestion:
    """Tests para get_or_create_rollover_suggestion."""

    def test_crea_sugerencia_si_balance_anterior_es_positivo(
        self, user, income_category, income_factory
    ):
        income_factory(user, income_category, amount=Decimal("1000.00"), date=date(2026, 1, 15))

        suggestion = get_or_create_rollover_suggestion(user, month=2, year=2026, start_day=1)

        assert suggestion is not None
        assert suggestion.status == RolloverSuggestionStatus.PENDING
        assert suggestion.amount == Decimal("1000.00")
        assert suggestion.period_start == date(2026, 1, 1)
        assert suggestion.period_end == date(2026, 2, 1)

    def test_no_crea_sugerencia_si_balance_anterior_es_cero_o_negativo(
        self, user, expense_category, expense_factory
    ):
        expense_factory(user, expense_category, amount=Decimal("500.00"), date=date(2026, 1, 10))

        suggestion = get_or_create_rollover_suggestion(user, month=2, year=2026, start_day=1)

        assert suggestion is None
        assert RolloverSuggestion.objects.count() == 0

    def test_no_duplica_si_ya_existe_para_ese_periodo(self, user, income_category, income_factory):
        income_factory(user, income_category, amount=Decimal("1000.00"), date=date(2026, 1, 15))

        first = get_or_create_rollover_suggestion(user, month=2, year=2026, start_day=1)
        second = get_or_create_rollover_suggestion(user, month=2, year=2026, start_day=1)

        assert first.pk == second.pk
        assert RolloverSuggestion.objects.count() == 1

    def test_retorna_sugerencia_existente_aunque_balance_actual_ya_no_sea_positivo(
        self, user, income_category, income_factory, expense_category, expense_factory
    ):
        """Si se agregan gastos retroactivos después de creada la sugerencia, no debe recalcularse."""
        income_factory(user, income_category, amount=Decimal("1000.00"), date=date(2026, 1, 15))
        first = get_or_create_rollover_suggestion(user, month=2, year=2026, start_day=1)

        expense_factory(user, expense_category, amount=Decimal("2000.00"), date=date(2026, 1, 20))
        second = get_or_create_rollover_suggestion(user, month=2, year=2026, start_day=1)

        assert second.pk == first.pk
        assert second.amount == Decimal("1000.00")


@pytest.mark.django_db
class TestGetDismissedAmountForCurrentPeriod:
    """Tests para get_dismissed_amount_for_current_period."""

    def test_retorna_monto_si_hay_sugerencia_descartada_del_periodo_anterior(self, user):
        suggestion = RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("1500.00"),
        )
        suggestion.mark_dismissed()

        amount = get_dismissed_amount_for_current_period(user, month=2, year=2026, start_day=1)

        assert amount == Decimal("1500.00")

    def test_retorna_none_si_la_sugerencia_esta_pendiente(self, user):
        RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("1500.00"),
        )

        amount = get_dismissed_amount_for_current_period(user, month=2, year=2026, start_day=1)

        assert amount is None

    def test_retorna_none_si_la_sugerencia_fue_depositada(self, user, saving):
        suggestion = RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("1500.00"),
        )
        suggestion.mark_deposited(saving)

        amount = get_dismissed_amount_for_current_period(user, month=2, year=2026, start_day=1)

        assert amount is None

    def test_retorna_none_un_periodo_despues_del_descarte(self, user):
        """El dato informativo no se arrastra más de un período."""
        suggestion = RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("1500.00"),
        )
        suggestion.mark_dismissed()

        amount = get_dismissed_amount_for_current_period(user, month=3, year=2026, start_day=1)

        assert amount is None

    def test_retorna_none_sin_sugerencias(self, user):
        amount = get_dismissed_amount_for_current_period(user, month=2, year=2026, start_day=1)

        assert amount is None


@pytest.mark.django_db
class TestGetOrCreateRolloverIncomeCategory:
    """Tests para get_or_create_rollover_income_category."""

    def test_crea_categoria_de_sistema(self):
        category = get_or_create_rollover_income_category()

        assert category.name == "Sobrante de mes anterior"
        assert category.is_system is True
        assert category.user is None
        assert category.type == "INCOME"

    def test_no_duplica_categoria_en_llamadas_sucesivas(self):
        first = get_or_create_rollover_income_category()
        second = get_or_create_rollover_income_category()

        assert first.pk == second.pk


@pytest.mark.django_db
class TestConfirmRolloverDeposit:
    """Tests para confirm_rollover_deposit (DT-067)."""

    def test_crea_deposito_y_marca_sugerencia(self, user, saving):
        suggestion = RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("1000.00"),
        )

        confirm_rollover_deposit(suggestion, saving)

        saving.refresh_from_db()
        suggestion.refresh_from_db()
        assert saving.current_amount == Decimal("1000.00")
        assert suggestion.status == RolloverSuggestionStatus.DEPOSITED
        assert suggestion.saving == saving

    def test_crea_income_compensatorio_en_ultimo_dia_del_periodo_anterior(self, user, saving):
        from apps.income.models import Income

        suggestion = RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("1000.00"),
        )

        confirm_rollover_deposit(suggestion, saving)

        income = Income.objects.get(user=user)
        assert income.amount == Decimal("1000.00")
        assert income.date == date(2026, 1, 31)
        assert income.category.name == "Sobrante de mes anterior"

    def test_balance_del_periodo_actual_no_se_ve_afectado(self, user, saving):
        """El depósito es un retiro contable del período actual, pero el
        Income compensatorio lo neutraliza para que el balance no quede negativo."""
        suggestion = RolloverSuggestion.objects.create(
            user=user,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 1),
            amount=Decimal("1000.00"),
        )

        confirm_rollover_deposit(suggestion, saving)

        balance = get_period_balance(user, date(2026, 2, 1), date(2026, 3, 1))
        assert balance == Decimal("0")
