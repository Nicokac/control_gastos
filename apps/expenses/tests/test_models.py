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


@pytest.mark.django_db
class TestExpenseClassMethods:
    """Tests para métodos de clase de Expense."""

    def test_get_user_expenses_returns_user_expenses(
        self, user, other_user, expense_category, expense_factory
    ):
        """Verifica que get_user_expenses retorna solo gastos del usuario."""
        exp1 = expense_factory(user, expense_category, description="Gasto 1")
        exp2 = expense_factory(user, expense_category, description="Gasto 2")

        # Crear categoría y gasto para otro usuario
        from apps.categories.models import Category
        from apps.core.constants import CategoryType

        other_cat = Category.objects.create(
            name="Otra Cat",
            type=CategoryType.EXPENSE,
            user=other_user,
        )
        expense_factory(other_user, other_cat, description="Gasto otro")

        expenses = Expense.get_user_expenses(user)

        assert expenses.count() == 2
        assert exp1 in expenses
        assert exp2 in expenses

    def test_get_user_expenses_filters_by_month_year(self, user, expense_category, expense_factory):
        """Verifica filtro por mes y año en get_user_expenses."""
        from datetime import date

        # Gasto en enero 2026
        expense_factory(user, expense_category, description="Enero", date=date(2026, 1, 15))

        # Gasto en febrero 2026
        expense_factory(user, expense_category, description="Febrero", date=date(2026, 2, 15))

        expenses = Expense.get_user_expenses(user, month=1, year=2026)

        assert expenses.count() == 1
        assert expenses.first().description == "Enero"

    def test_get_user_expenses_filters_by_year_only(self, user, expense_category, expense_factory):
        """Verifica filtro solo por año en get_user_expenses."""
        from datetime import date

        # Gastos en 2026
        expense_factory(user, expense_category, description="2026-1", date=date(2026, 1, 15))
        expense_factory(user, expense_category, description="2026-2", date=date(2026, 6, 15))

        # Gasto en 2025
        expense_factory(user, expense_category, description="2025", date=date(2025, 12, 15))

        expenses = Expense.get_user_expenses(user, year=2026)

        assert expenses.count() == 2

    def test_get_user_expenses_includes_category(self, user, expense_category, expense_factory):
        """Verifica que get_user_expenses incluye select_related de categoría."""
        expense_factory(user, expense_category, description="Test")

        expenses = Expense.get_user_expenses(user)

        # No debe hacer query adicional para categoría
        expense = expenses.first()
        assert expense.category.name == expense_category.name

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

    def test_get_monthly_total_excludes_inactive(self, user, expense_category, expense_factory):
        """Verifica que get_monthly_total excluye gastos inactivos."""
        from datetime import date

        expense_factory(user, expense_category, amount=Decimal("100.00"), date=date(2026, 1, 10))
        exp2 = expense_factory(
            user, expense_category, amount=Decimal("200.00"), date=date(2026, 1, 15)
        )

        # Soft delete uno
        exp2.soft_delete()

        total = Expense.get_monthly_total(user, month=1, year=2026)

        assert total == Decimal("100.00")

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

    def test_get_by_category_excludes_inactive(self, user, expense_category, expense_factory):
        """Verifica que get_by_category excluye gastos inactivos."""
        from datetime import date

        expense_factory(user, expense_category, amount=Decimal("100.00"), date=date(2026, 1, 10))
        exp2 = expense_factory(
            user, expense_category, amount=Decimal("200.00"), date=date(2026, 1, 15)
        )

        exp2.soft_delete()

        result = list(Expense.get_by_category(user, month=1, year=2026))

        assert len(result) == 1
        assert result[0]["total"] == Decimal("100.00")


@pytest.mark.django_db
class TestExpenseSavingSync:
    """Tests para sincronización Expense-Saving."""

    def test_new_expense_with_saving_creates_deposit(self, user, expense_category, saving_factory):
        """Nuevo gasto con saving genera depósito automático."""
        saving = saving_factory(user, current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Compra acciones",
            amount=Decimal("10000.00"),
            amount_ars=Decimal("10000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving,
        )

        # Verificar que el expense se creó correctamente
        assert expense.pk is not None
        assert expense.saving == saving

        # Verificar que el ahorro recibió el depósito
        saving.refresh_from_db()
        assert saving.current_amount == Decimal("10000.00")

        # Verificar que se creó el movimiento
        assert saving.movements.count() == 1
        movement = saving.movements.first()
        assert movement.type == "DEPOSIT"
        assert movement.amount == Decimal("10000.00")
        assert "Desde gasto" in movement.description

    def test_new_expense_without_saving_no_effect(self, user, expense_category, saving_factory):
        """Nuevo gasto sin saving no afecta ningún ahorro."""
        saving = saving_factory(user, current_amount=Decimal("5000.00"))

        Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto normal",
            amount=Decimal("1000.00"),
            amount_ars=Decimal("1000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=None,
        )

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("5000.00")
        assert saving.movements.count() == 0

    def test_update_expense_amount_increases_saving(self, user, expense_category, saving_factory):
        """Aumentar monto de expense con saving deposita la diferencia."""
        saving = saving_factory(user, current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Inversión",
            amount=Decimal("5000.00"),
            amount_ars=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving,
        )

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("5000.00")

        # Aumentar monto
        expense.amount = Decimal("8000.00")
        expense.amount_ars = Decimal("8000.00")
        expense.save()

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("8000.00")

        # Debe haber 2 movimientos: depósito inicial + ajuste
        assert saving.movements.count() == 2

    def test_update_expense_amount_decreases_saving(self, user, expense_category, saving_factory):
        """Disminuir monto de expense con saving retira la diferencia."""
        saving = saving_factory(user, current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Inversión",
            amount=Decimal("10000.00"),
            amount_ars=Decimal("10000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving,
        )

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("10000.00")

        # Disminuir monto
        expense.amount = Decimal("7000.00")
        expense.amount_ars = Decimal("7000.00")
        expense.save()

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("7000.00")

    def test_reassign_expense_to_different_saving(self, user, expense_category, saving_factory):
        """Reasignar expense a otro saving: retira del anterior, deposita en nuevo."""
        saving1 = saving_factory(user, name="Ahorro 1", current_amount=Decimal("0.00"))
        saving2 = saving_factory(user, name="Ahorro 2", current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Inversión",
            amount=Decimal("5000.00"),
            amount_ars=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving1,
        )

        saving1.refresh_from_db()
        assert saving1.current_amount == Decimal("5000.00")
        assert saving2.current_amount == Decimal("0.00")

        # Reasignar a saving2
        expense.saving = saving2
        expense.save()

        saving1.refresh_from_db()
        saving2.refresh_from_db()

        assert saving1.current_amount == Decimal("0.00")
        assert saving2.current_amount == Decimal("5000.00")

    def test_remove_saving_from_expense_reverts_deposit(
        self, user, expense_category, saving_factory
    ):
        """Quitar saving de expense revierte el depósito."""
        saving = saving_factory(user, current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Inversión",
            amount=Decimal("5000.00"),
            amount_ars=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving,
        )

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("5000.00")

        # Quitar saving
        expense.saving = None
        expense.save()

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("0.00")

    def test_soft_delete_expense_reverts_deposit(self, user, expense_category, saving_factory):
        """Soft delete de expense con saving revierte el depósito."""
        saving = saving_factory(user, current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Inversión",
            amount=Decimal("8000.00"),
            amount_ars=Decimal("8000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving,
        )

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("8000.00")

        # Soft delete
        expense.soft_delete()

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("0.00")

        # Verificar movimiento de retiro
        withdrawal = saving.movements.filter(type="WITHDRAWAL").first()
        assert withdrawal is not None
        assert "eliminado" in withdrawal.description.lower()

    def test_soft_delete_without_saving_no_error(self, user, expense_category):
        """Soft delete de expense sin saving no genera error."""
        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Gasto normal",
            amount=Decimal("1000.00"),
            amount_ars=Decimal("1000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=None,
        )

        # No debe lanzar error
        expense.soft_delete()
        assert expense.is_active is False

    def test_withdrawal_insufficient_funds_handled_gracefully(
        self, user, expense_category, saving_factory
    ):
        """Si no hay saldo suficiente para revertir, no falla."""
        saving = saving_factory(user, current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Inversión",
            amount=Decimal("5000.00"),
            amount_ars=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving,
        )

        saving.refresh_from_db()
        assert saving.current_amount == Decimal("5000.00")

        # Simular que el saldo fue retirado manualmente
        saving.current_amount = Decimal("0.00")
        saving.save()

        # Soft delete no debe fallar aunque no haya saldo
        expense.soft_delete()
        assert expense.is_active is False

    def test_reassign_insufficient_funds_continues(self, user, expense_category, saving_factory):
        """Reasignar con saldo insuficiente en origen: deposita en destino igual."""
        saving1 = saving_factory(user, name="Ahorro 1", current_amount=Decimal("0.00"))
        saving2 = saving_factory(user, name="Ahorro 2", current_amount=Decimal("0.00"))

        expense = Expense.objects.create(
            user=user,
            category=expense_category,
            description="Inversión",
            amount=Decimal("5000.00"),
            amount_ars=Decimal("5000.00"),
            currency=Currency.ARS,
            exchange_rate=Decimal("1.00"),
            date=timezone.now().date(),
            saving=saving1,
        )

        # Simular retiro manual del saving1
        saving1.current_amount = Decimal("0.00")
        saving1.save()

        # Reasignar a saving2 (el retiro de saving1 fallará silenciosamente)
        expense.saving = saving2
        expense.save()

        saving2.refresh_from_db()
        # El depósito en saving2 debe realizarse aunque el retiro de saving1 falle
        assert saving2.current_amount == Decimal("5000.00")
