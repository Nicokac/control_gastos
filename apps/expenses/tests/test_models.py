"""
Tests para el modelo Expense.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

import pytest

from apps.core.constants import Currency
from apps.expenses.models import Expense


@pytest.mark.django_db
class TestExpenseModel:
    """Tests para el modelo Expense."""

    def test_create_expense_ars(self, user, expense_category):
        """Verifica creación de gasto en ARS."""
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Compra supermercado",
            amount=Decimal("1500.50"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        assert expense.pk is not None
        assert expense.amount == Decimal("1500.50")
        assert expense.currency == Currency.ARS
        assert expense.amount_ars == Decimal("1500.50")

    def test_create_expense_usd(self, user, expense_category):
        """Verifica creación de gasto en USD con conversión."""
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Compra Amazon",
            amount=Decimal("100.00"),
            currency=Currency.USD,
            exchange_rate=Decimal("1150.00"),
            date=timezone.now().date(),
        )

        assert expense.currency == Currency.USD
        assert expense.amount_ars == Decimal("115000.00")

    def test_expense_str(self, expense):
        """Verifica representación string."""
        result = str(expense)

        assert expense.description in result or str(expense.amount) in result

    def test_expense_formatted_amount(self, user, expense_category):
        """Verifica formato de monto."""
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Test",
            amount=Decimal("1500.50"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        formatted = expense.formatted_amount
        assert "$" in formatted or "1500" in formatted

    def test_expense_belongs_to_user(self, expense, user):
        """Verifica que el gasto pertenece al usuario."""
        assert expense.user == user

    def test_expense_belongs_to_category(self, expense, expense_category):
        """Verifica que el gasto pertenece a la categoría."""
        assert expense.category == expense_category

    def test_expense_soft_delete(self, expense):
        """Verifica soft delete de gasto."""
        expense_id = expense.pk
        expense.soft_delete()

        assert expense.is_active is False
        assert Expense.objects.filter(pk=expense_id).exists() is False
        assert Expense.all_objects.filter(pk=expense_id).exists() is True

    def test_expense_timestamps(self, expense):
        """Verifica timestamps."""
        assert expense.created_at is not None
        assert expense.updated_at is not None

    def test_expense_date_required(self, user, expense_category):
        """Verifica que la fecha es requerida."""
        with pytest.raises(Exception):
            Expense.objects.create(
                user=user,
                category=expense_category,
                description="Sin fecha",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                exchange_rate=Decimal("1.00"),
                date=None,
            )


@pytest.mark.django_db
class TestExpenseCalculations:
    """Tests para cálculos de Expense."""

    def test_amount_ars_calculation_usd(self, user, expense_category):
        """Verifica cálculo de amount_ars para USD."""
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Test USD",
            amount=Decimal("50.00"),
            currency=Currency.USD,
            exchange_rate=Decimal("1200.00"),
            date=timezone.now().date(),
        )

        assert expense.amount_ars == Decimal("60000.00")

    def test_amount_ars_calculation_ars(self, user, expense_category):
        """Verifica cálculo de amount_ars para ARS."""
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Test ARS",
            amount=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        assert expense.amount_ars == Decimal("5000.00")

    def test_exchange_rate_default(self, user, expense_category):
        """Verifica tipo de cambio por defecto para ARS."""
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Test",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            date=timezone.now().date(),
        )

        # El exchange_rate debería ser 1 para ARS o el default
        assert expense.exchange_rate >= Decimal("1.00")


@pytest.mark.django_db
class TestExpenseQuerySet:
    """Tests para el QuerySet de Expense."""

    def test_filter_by_user(self, user, other_user, expense_category, expense_factory):
        """Verifica filtro por usuario."""
        exp_user1 = expense_factory(user, expense_category, description="User 1")

        other_category = expense_category
        other_category.pk = None
        other_category.user = other_user
        other_category.save()

        exp_user2 = expense_factory(other_user, other_category, description="User 2")

        user_expenses = Expense.objects.filter(user=user)

        assert exp_user1 in user_expenses
        assert exp_user2 not in user_expenses

    def test_filter_by_category(
        self, user, expense_category, expense_category_factory, expense_factory
    ):
        """Verifica filtro por categoría."""
        cat2 = expense_category_factory(user, name="Otra Categoría")

        exp1 = expense_factory(user, expense_category, description="Cat 1")
        exp2 = expense_factory(user, cat2, description="Cat 2")

        cat_expenses = Expense.objects.filter(category=expense_category)

        assert exp1 in cat_expenses
        assert exp2 not in cat_expenses

    def test_filter_by_date_range(self, user, expense_category, expense_factory, today, yesterday):
        """Verifica filtro por rango de fechas."""
        exp_today = expense_factory(user, expense_category, date=today)
        exp_yesterday = expense_factory(user, expense_category, date=yesterday)

        today_expenses = Expense.objects.filter(date=today)

        assert exp_today in today_expenses
        assert exp_yesterday not in today_expenses

    def test_filter_by_month_year(self, user, expense_category, expense_factory, today):
        """Verifica filtro por mes y año."""
        expense = expense_factory(user, expense_category, date=today)

        month_expenses = Expense.objects.filter(date__month=today.month, date__year=today.year)

        assert expense in month_expenses

    def test_sum_by_category(self, user, expense_category, expense_factory):
        """Verifica suma de gastos por categoría."""
        from django.db.models import Sum

        expense_factory(user, expense_category, amount=Decimal("100.00"))
        expense_factory(user, expense_category, amount=Decimal("200.00"))
        expense_factory(user, expense_category, amount=Decimal("300.00"))

        total = Expense.objects.filter(user=user, category=expense_category).aggregate(
            total=Sum("amount_ars")
        )["total"]

        assert total == Decimal("600.00")


@pytest.mark.django_db
class TestExpenseValidations:
    """Tests de validaciones del modelo Expense."""

    def test_negative_amount_raises_error(self, user, expense_category):
        """Verifica que monto negativo lance error."""
        expense = Expense(
            user=user,
            category=expense_category,
            description="Monto negativo",
            amount=Decimal("-100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError):
            expense.full_clean()

    def test_zero_amount_raises_error(self, user, expense_category):
        """Verifica que monto cero lance error."""
        expense = Expense(
            user=user,
            category=expense_category,
            description="Monto cero",
            amount=Decimal("0.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError):
            expense.full_clean()

    def test_usd_requires_exchange_rate(self, user, expense_category):
        """Verifica que USD requiera exchange_rate."""
        expense = Expense(
            user=user,
            category=expense_category,
            description="Compra USD sin TC",
            amount=Decimal("100.00"),
            currency=Currency.USD,
            exchange_rate=None,
            date=timezone.now().date(),
        )

        with pytest.raises((ValidationError, IntegrityError)):
            expense.full_clean()
            expense.save()

    # def test_usd_exchange_rate_must_be_positive(self, user, expense_category):
    #     """Verifica que exchange_rate sea positivo para USD."""
    #     expense = Expense(
    #         user=user,
    #         category=expense_category,
    #         description='Compra USD TC cero',
    #         amount=Decimal('100.00'),
    #         currency=Currency.USD,
    #         exchange_rate=Decimal('0.00'),
    #         date=timezone.now().date()
    #     )

    #     with pytest.raises(ValidationError):
    #         expense.full_clean()

    def test_ars_allows_default_exchange_rate(self, user, expense_category):
        """Verifica que ARS permita exchange_rate por defecto."""
        expense = Expense(
            user=user,
            category=expense_category,
            description="Gasto ARS",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        # No debería lanzar error
        expense.full_clean()
        expense.save()

        assert expense.pk is not None

    def test_description_required(self, user, expense_category):
        """Verifica que descripción sea requerida."""
        expense = Expense(
            user=user,
            category=expense_category,
            description="",  # Vacío
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError):
            expense.full_clean()

    def test_category_required(self, user):
        """Verifica que categoría sea requerida."""
        with pytest.raises((ValidationError, IntegrityError)):
            expense = Expense(
                user=user,
                category=None,
                description="Sin categoría",
                amount=Decimal("100.00"),
                currency=Currency.ARS,
                exchange_rate=Decimal("1.00"),
                date=timezone.now().date(),
            )
            expense.full_clean()
            expense.save()
