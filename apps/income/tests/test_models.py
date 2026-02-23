"""
Tests para el modelo Income.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

import pytest

from apps.core.constants import Currency
from apps.income.models import Income


@pytest.mark.django_db
class TestIncomeModel:
    """Tests para el modelo Income."""

    def test_create_income_ars(self, user, income_category):
        """Verifica creación de ingreso en ARS."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description="Sueldo mensual",
            amount=Decimal("150000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        assert income.pk is not None
        assert income.amount == Decimal("150000.00")
        assert income.currency == Currency.ARS
        assert income.amount_ars == Decimal("150000.00")

    def test_create_income_usd(self, user, income_category):
        """Verifica creación de ingreso en USD con conversión."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description="Freelance",
            amount=Decimal("500.00"),
            currency=Currency.USD,
            exchange_rate=Decimal("1150.00"),
            date=timezone.now().date(),
        )

        assert income.currency == Currency.USD
        assert income.amount_ars == Decimal("575000.00")

    def test_income_str(self, income):
        """Verifica representación string."""
        result = str(income)

        assert income.description in result or str(income.amount) in result

    def test_income_formatted_amount(self, user, income_category):
        """Verifica formato de monto."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description="Test",
            amount=Decimal("50000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        formatted = income.formatted_amount
        assert "$" in formatted or "50000" in formatted

    def test_income_belongs_to_user(self, income, user):
        """Verifica que el ingreso pertenece al usuario."""
        assert income.user == user

    def test_income_timestamps(self, income):
        """Verifica timestamps."""
        assert income.created_at is not None
        assert income.updated_at is not None


@pytest.mark.django_db
class TestIncomeCalculations:
    """Tests para cálculos de Income."""

    def test_amount_ars_calculation_usd(self, user, income_category):
        """Verifica cálculo de amount_ars para USD."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description="Test USD",
            amount=Decimal("100.00"),
            currency=Currency.USD,
            exchange_rate=Decimal("1200.00"),
            date=timezone.now().date(),
        )

        assert income.amount_ars == Decimal("120000.00")

    def test_amount_ars_calculation_ars(self, user, income_category):
        """Verifica cálculo de amount_ars para ARS."""
        income = Income.objects.create(
            user=user,
            category=income_category,
            description="Test ARS",
            amount=Decimal("80000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        assert income.amount_ars == Decimal("80000.00")


@pytest.mark.django_db
class TestIncomeQuerySet:
    """Tests para el QuerySet de Income."""

    def test_filter_by_user(
        self, user, other_user, income_category, income_category_factory, income_factory
    ):
        """Verifica filtro por usuario."""
        inc_user1 = income_factory(user, income_category, description="User 1")

        other_category = income_category_factory(other_user, name="Salario Other")
        inc_user2 = income_factory(other_user, other_category, description="User 2")

        user_incomes = Income.objects.filter(user=user)

        assert inc_user1 in user_incomes
        assert inc_user2 not in user_incomes

    def test_filter_by_month_year(self, user, income_category, income_factory, today):
        """Verifica filtro por mes y año."""
        income = income_factory(user, income_category, date=today)

        month_incomes = Income.objects.filter(date__month=today.month, date__year=today.year)

        assert income in month_incomes

    def test_sum_total_income(self, user, income_category, income_factory):
        """Verifica suma total de ingresos."""
        from django.db.models import Sum

        income_factory(user, income_category, amount=Decimal("50000.00"))
        income_factory(user, income_category, amount=Decimal("30000.00"))

        total = Income.objects.filter(user=user).aggregate(total=Sum("amount_ars"))["total"]

        assert total == Decimal("80000.00")


@pytest.mark.django_db
class TestIncomeValidations:
    """Tests de validaciones del modelo Income."""

    def test_negative_amount_raises_error(self, user, income_category):
        """Verifica que monto negativo lance error."""
        income = Income(
            user=user,
            category=income_category,
            description="Monto negativo",
            amount=Decimal("-100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError):
            income.full_clean()

    def test_zero_amount_raises_error(self, user, income_category):
        """Verifica que monto cero lance error."""
        income = Income(
            user=user,
            category=income_category,
            description="Monto cero",
            amount=Decimal("0.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError):
            income.full_clean()

    def test_usd_requires_exchange_rate(self, user, income_category):
        """Verifica que USD requiera exchange_rate."""
        income = Income(
            user=user,
            category=income_category,
            description="Ingreso USD sin TC",
            amount=Decimal("100.00"),
            currency=Currency.USD,
            exchange_rate=None,
            date=timezone.now().date(),
        )

        with pytest.raises((ValidationError, IntegrityError)):
            income.full_clean()
            income.save()

    # def test_usd_exchange_rate_must_be_positive(self, user, income_category):
    #     """Verifica que exchange_rate sea positivo para USD."""
    #     income = Income(
    #         user=user,
    #         category=income_category,
    #         description='Ingreso USD TC cero',
    #         amount=Decimal('100.00'),
    #         currency=Currency.USD,
    #         exchange_rate=Decimal('0.00'),
    #         date=timezone.now().date()
    #     )

    #     with pytest.raises(ValidationError):
    #         income.full_clean()

    def test_ars_allows_default_exchange_rate(self, user, income_category):
        """Verifica que ARS permita exchange_rate por defecto."""
        income = Income(
            user=user,
            category=income_category,
            description="Ingreso ARS",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        # No debería lanzar error
        income.full_clean()
        income.save()

        assert income.pk is not None

    def test_description_required(self, user, income_category):
        """Verifica que descripción sea requerida."""
        income = Income(
            user=user,
            category=income_category,
            description="",  # Vacío
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError):
            income.full_clean()


@pytest.mark.django_db
class TestIncomeCategoryValidation:
    """Tests para validación de categoría en Income."""

    def test_income_requires_income_category(self, user, expense_category):
        """No se puede crear income con categoría de gasto."""
        income = Income(
            user=user,
            category=expense_category,  # Categoría EXPENSE
            description="Ingreso con categoría incorrecta",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError) as exc_info:
            income.full_clean()

        assert "category" in exc_info.value.message_dict

    def test_income_accepts_income_category(self, user, income_category):
        """Se puede crear income con categoría de ingreso."""
        income = Income(
            user=user,
            category=income_category,
            description="Ingreso válido",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        income.full_clean()
        income.save()
        assert income.pk is not None

    def test_clean_category_does_not_raise_if_category_missing(self, user):
        """
        Si category_id apunta a una categoría inexistente, Income.clean() no debe explotar
        (tu código hace try/except DoesNotExist y hace pass).
        OJO: no usamos full_clean() porque Django valida el FK y falla antes.
        """
        income = Income(
            user=user,
            category_id=999999,  # no existe
            description="Ingreso con category inexistente",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        # Ejecutar SOLO la validación custom del modelo
        income.clean()  # No debería lanzar


@pytest.mark.django_db
class TestIncomeClassMethods:
    """Tests para métodos de clase de Income."""

    def test_get_user_incomes_returns_only_user_incomes(
        self, user, other_user, income_category_factory, income_factory
    ):
        cat_user = income_category_factory(user, name="Sueldo")
        cat_other = income_category_factory(other_user, name="Sueldo Other")

        inc1 = income_factory(user, cat_user, description="Ingreso 1")
        inc2 = income_factory(user, cat_user, description="Ingreso 2")
        income_factory(other_user, cat_other, description="Ingreso otro")

        qs = Income.get_user_incomes(user)

        assert qs.count() == 2
        assert inc1 in qs
        assert inc2 in qs

    def test_get_user_incomes_filters_by_month_year(self, user, income_category, income_factory):
        inc_jan = income_factory(user, income_category, description="Enero", date=date(2026, 1, 15))
        income_factory(user, income_category, description="Febrero", date=date(2026, 2, 15))

        qs = Income.get_user_incomes(user, month=1, year=2026)

        assert qs.count() == 1
        assert inc_jan in qs

    def test_get_user_incomes_filters_by_year_only(self, user, income_category, income_factory):
        income_factory(user, income_category, description="2026-1", date=date(2026, 1, 15))
        income_factory(user, income_category, description="2026-2", date=date(2026, 6, 15))
        income_factory(user, income_category, description="2025", date=date(2025, 12, 15))

        qs = Income.get_user_incomes(user, year=2026)

        assert qs.count() == 2

    def test_get_user_incomes_select_related_category(
        self, user, income_category, income_factory, django_assert_num_queries
    ):
        """
        get_user_incomes hace select_related('category').
        Validamos que acceder a category no dispare query extra (best-effort).
        """
        income_factory(user, income_category, description="Ingreso")

        with django_assert_num_queries(1):
            inc = Income.get_user_incomes(user).first()
            _ = inc.category.name

    def test_get_monthly_total_sums_correctly(self, user, income_category, income_factory):
        income_factory(user, income_category, amount=Decimal("100.00"), date=date(2026, 1, 10))
        income_factory(user, income_category, amount=Decimal("200.00"), date=date(2026, 1, 15))
        income_factory(user, income_category, amount=Decimal("300.00"), date=date(2026, 1, 20))

        total = Income.get_monthly_total(user, month=1, year=2026)

        assert total == Decimal("600.00")

    def test_get_monthly_total_returns_zero_if_no_incomes(self, user):
        total = Income.get_monthly_total(user, month=1, year=2026)
        assert total == Decimal("0")

    def test_get_monthly_total_excludes_other_months(self, user, income_category, income_factory):
        income_factory(user, income_category, amount=Decimal("100.00"), date=date(2026, 1, 10))
        income_factory(user, income_category, amount=Decimal("500.00"), date=date(2026, 2, 10))

        total = Income.get_monthly_total(user, month=1, year=2026)

        assert total == Decimal("100.00")

    def test_get_by_category_groups_and_orders(self, user, income_category_factory, income_factory):
        cat1 = income_category_factory(user, name="Sueldo")
        cat2 = income_category_factory(user, name="Freelance")

        income_factory(user, cat1, amount=Decimal("100.00"), date=date(2026, 1, 10))
        income_factory(user, cat1, amount=Decimal("150.00"), date=date(2026, 1, 15))
        income_factory(user, cat2, amount=Decimal("50.00"), date=date(2026, 1, 10))

        result = list(Income.get_by_category(user, month=1, year=2026))

        assert len(result) == 2
        assert result[0]["category__name"] == "Sueldo"
        assert result[0]["total"] == Decimal("250.00")
        assert result[1]["category__name"] == "Freelance"
        assert result[1]["total"] == Decimal("50.00")

    def test_get_by_category_returns_empty_if_no_incomes(self, user):
        result = list(Income.get_by_category(user, month=1, year=2026))
        assert result == []
