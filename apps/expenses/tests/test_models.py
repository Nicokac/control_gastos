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

    def test_expense_timestamps(self, expense):
        """Verifica timestamps."""
        assert expense.created_at is not None
        assert expense.updated_at is not None

    def test_expense_date_required(self, user, expense_category):  # 🔧 B017
        """Verifica que la fecha es requerida."""
        with pytest.raises((ValidationError, IntegrityError)):
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

    def test_description_optional(self, user, expense_category):
        """Verifica que descripción vacía es permitida."""
        expense = Expense(
            user=user,
            category=expense_category,
            description="",  # Vacío - ahora permitido
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )
        # No debe lanzar ValidationError
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


@pytest.mark.django_db
class TestExpenseCategoryValidation:
    """Tests para validación de categoría en Expense."""

    def test_expense_requires_expense_category(self, user, income_category):
        """Verifica que no se puede crear gasto con categoría de ingreso."""
        expense = Expense(
            user=user,
            category=income_category,  # Categoría de tipo INCOME
            description="Gasto con categoría incorrecta",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        with pytest.raises(ValidationError) as exc_info:
            expense.full_clean()

        assert "category" in exc_info.value.message_dict

    def test_expense_accepts_expense_category(self, user, expense_category):
        """Verifica que se puede crear gasto con categoría de gasto."""
        expense = Expense(
            user=user,
            category=expense_category,
            description="Gasto válido",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        # No debe lanzar error
        expense.full_clean()
        expense.save()
        assert expense.pk is not None

    def test_clean_does_not_call_category_objects_get(self, user, expense_category, monkeypatch):
        """Verifica que clean() no ejecuta lookup extra por Category.objects.get()."""
        from apps.categories.models import Category

        def _forbidden_get(*args, **kwargs):
            raise AssertionError("Category.objects.get() no debe usarse en Expense.clean()")

        monkeypatch.setattr(Category.objects, "get", _forbidden_get)

        expense = Expense(
            user=user,
            category=expense_category,
            description="Sin query extra",
            amount=Decimal("100.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
        )

        expense.full_clean()


@pytest.mark.django_db
class TestExpenseClassMethods:
    """Tests para métodos de clase de Expense."""

    def test_get_monthly_total_calculates_sum(self, user, expense_category, expense_factory):
        """Verifica que get_monthly_total suma correctamente."""
        from datetime import date

        expense_factory(user, expense_category, amount=Decimal("100.00"), date=date(2026, 1, 10))
        expense_factory(user, expense_category, amount=Decimal("200.00"), date=date(2026, 1, 15))
        expense_factory(user, expense_category, amount=Decimal("300.00"), date=date(2026, 1, 20))

        total = Expense.get_monthly_total(user, month=1, year=2026)

        assert total == Decimal("600.00")

    def test_get_monthly_total_returns_zero_if_no_expenses(self, user):
        """Verifica que get_monthly_total retorna 0 si no hay gastos."""
        total = Expense.get_monthly_total(user, month=1, year=2026)

        assert total == Decimal("0")

    def test_get_monthly_total_excludes_other_months(self, user, expense_category, expense_factory):
        """Verifica que get_monthly_total solo incluye el mes especificado."""
        from datetime import date

        expense_factory(user, expense_category, amount=Decimal("100.00"), date=date(2026, 1, 10))
        expense_factory(user, expense_category, amount=Decimal("500.00"), date=date(2026, 2, 10))

        total = Expense.get_monthly_total(user, month=1, year=2026)

        assert total == Decimal("100.00")

    def test_get_by_category_groups_correctly(
        self, user, expense_category_factory, expense_factory
    ):
        """Verifica que get_by_category agrupa por categoría."""
        from datetime import date

        cat1 = expense_category_factory(user, name="Comida")
        cat2 = expense_category_factory(user, name="Transporte")

        expense_factory(user, cat1, amount=Decimal("100.00"), date=date(2026, 1, 10))
        expense_factory(user, cat1, amount=Decimal("150.00"), date=date(2026, 1, 15))
        expense_factory(user, cat2, amount=Decimal("50.00"), date=date(2026, 1, 10))

        result = list(Expense.get_by_category(user, month=1, year=2026))

        assert len(result) == 2

        # Ordenado por total descendente
        assert result[0]["category__name"] == "Comida"
        assert result[0]["total"] == Decimal("250.00")
        assert result[1]["category__name"] == "Transporte"
        assert result[1]["total"] == Decimal("50.00")

    def test_get_by_category_returns_empty_if_no_expenses(self, user):
        """Verifica que get_by_category retorna vacío si no hay gastos."""
        result = list(Expense.get_by_category(user, month=1, year=2026))

        assert result == []
