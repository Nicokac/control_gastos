"""
Tests para el modelo Budget.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

import pytest

from apps.budgets.models import Budget


@pytest.mark.django_db
class TestBudgetModel:
    """Tests para el modelo Budget."""

    def test_create_budget(self, user, expense_category):
        """Verifica creación de presupuesto."""
        today = timezone.now().date()
        budget = Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("50000.00"),
            alert_threshold=80,
        )

        assert budget.pk is not None
        assert budget.amount == Decimal("50000.00")
        assert budget.alert_threshold == 80

    def test_budget_str(self, budget):
        """Verifica representación string."""
        result = str(budget)

        assert budget.category.name in result or str(budget.amount) in result

    def test_budget_default_alert_threshold(self, user, expense_category):
        """Verifica umbral de alerta por defecto."""
        today = timezone.now().date()
        budget = Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("10000.00"),
        )

        assert budget.alert_threshold == 80

    def test_budget_timestamps(self, budget):
        """Verifica timestamps."""
        assert budget.created_at is not None
        assert budget.updated_at is not None

    def test_budget_unique_per_category_month_year(self, user, expense_category):
        """Verifica unicidad por categoría/mes/año."""
        today = timezone.now().date()

        Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("10000.00"),
        )

        with pytest.raises(ValidationError):  # 🔧 B017
            Budget.objects.create(
                user=user,
                category=expense_category,
                month=today.month,
                year=today.year,
                amount=Decimal("20000.00"),
            )


@pytest.mark.django_db
class TestBudgetCalculations:
    """Tests para cálculos de Budget."""

    def test_spent_amount_no_expenses(self, budget):
        """Verifica spent_amount sin gastos."""
        assert budget.spent_amount == Decimal("0")

    def test_spent_amount_with_expenses(
        self, user, expense_category, budget_factory, expense_factory
    ):
        """Verifica spent_amount con gastos."""
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("2000.00"), date=today)
        expense_factory(user, expense_category, amount=Decimal("3000.00"), date=today)

        assert budget.spent_amount == Decimal("5000.00")

    def test_remaining_amount(self, user, expense_category, budget_factory, expense_factory):
        """Verifica monto restante."""
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("3000.00"), date=today)

        assert budget.remaining_amount == Decimal("7000.00")

    def test_spent_percentage_zero(self, budget):
        """Verifica porcentaje gastado en cero."""
        assert budget.spent_percentage == 0

    def test_spent_percentage_partial(
        self, user, expense_category, budget_factory, expense_factory
    ):
        """Verifica porcentaje gastado parcial."""
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("5000.00"), date=today)

        assert budget.spent_percentage == 50

    def test_spent_percentage_over_budget(
        self, user, expense_category, budget_factory, expense_factory
    ):
        """Verifica porcentaje cuando se excede el presupuesto."""
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("15000.00"), date=today)

        assert budget.spent_percentage == 150


@pytest.mark.django_db
class TestBudgetStatus:
    """Tests para el estado del presupuesto."""

    def test_is_over_budget_false(self, budget):
        """Verifica is_over_budget cuando no se excede."""
        assert budget.is_over_budget is False

    def test_is_over_budget_true(self, user, expense_category, budget_factory, expense_factory):
        """Verifica is_over_budget cuando se excede."""
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("12000.00"), date=today)

        assert budget.is_over_budget is True

    def test_is_near_limit_false(self, budget):
        """Verifica is_near_limit cuando está lejos del límite."""
        assert budget.is_near_limit is False

    def test_is_near_limit_true(self, user, expense_category, budget_factory, expense_factory):
        """Verifica is_near_limit cuando está cerca del límite."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("10000.00"),
            alert_threshold=80,
        )

        # 85% gastado
        expense_factory(user, expense_category, amount=Decimal("8500.00"), date=today)

        assert budget.is_near_limit is True
        assert budget.is_over_budget is False

    def test_status_ok(self, budget):
        """Verifica status OK."""
        assert budget.status == "ok"

    def test_status_warning(self, user, expense_category, budget_factory, expense_factory):
        """Verifica status warning."""
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("10000.00"),
            alert_threshold=80,
        )

        expense_factory(user, expense_category, amount=Decimal("8500.00"), date=today)

        assert budget.status == "warning"

    def test_status_over(self, user, expense_category, budget_factory, expense_factory):
        """Verifica status over."""
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("12000.00"), date=today)

        assert budget.status == "over"


@pytest.mark.django_db
class TestBudgetQuerySet:
    """Tests para el QuerySet de Budget."""

    def test_filter_by_user(
        self, user, other_user, expense_category, expense_category_factory, budget_factory
    ):
        """Verifica filtro por usuario."""
        budget_user1 = budget_factory(user, expense_category)

        other_cat = expense_category_factory(other_user, name="Other Cat")
        budget_user2 = budget_factory(other_user, other_cat)

        user_budgets = Budget.objects.filter(user=user)

        assert budget_user1 in user_budgets
        assert budget_user2 not in user_budgets

    def test_filter_by_month_year(
        self, user, expense_category, budget_factory, current_month, current_year
    ):
        """Verifica filtro por mes y año."""
        budget = budget_factory(user, expense_category, month=current_month, year=current_year)

        month_budgets = Budget.objects.filter(user=user, month=current_month, year=current_year)

        assert budget in month_budgets

    def test_get_with_spent(self, user, expense_category, budget_factory, expense_factory):
        """Verifica método get_with_spent."""
        today = timezone.now().date()
        budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("3000.00"), date=today)

        budgets = Budget.get_with_spent(user, month=today.month, year=today.year)

        assert budgets.count() == 1
        assert budgets.first().spent_amount == Decimal("3000.00")


@pytest.mark.django_db
class TestBudgetConstraints:
    """Tests para constraints del modelo Budget."""

    def test_unique_budget_per_category_month_year(self, user, expense_category):
        """Verifica constraint único por usuario/categoría/mes/año."""
        today = timezone.now().date()

        Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("5000.00"),
        )

        # Lanza ValidationError porque full_clean() se llama en save()
        with pytest.raises(ValidationError):
            Budget.objects.create(
                user=user,
                category=expense_category,
                month=today.month,
                year=today.year,
                amount=Decimal("10000.00"),
            )

    def test_same_category_different_month_allowed(self, user, expense_category):
        """Verifica que misma categoría en diferente mes sea permitido."""
        today = timezone.now().date()

        Budget.objects.create(
            user=user,
            category=expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("5000.00"),
        )

        # Calcular próximo mes
        if today.month == 12:
            next_month = 1
            next_year = today.year + 1
        else:
            next_month = today.month + 1
            next_year = today.year

        # Diferente mes debería funcionar
        budget2 = Budget.objects.create(
            user=user,
            category=expense_category,
            month=next_month,
            year=next_year,
            amount=Decimal("7000.00"),
        )

        assert budget2.pk is not None

    def test_same_month_different_category_allowed(self, user, expense_category_factory):
        """Verifica que mismo mes con diferente categoría sea permitido."""
        today = timezone.now().date()

        cat1 = expense_category_factory(user, name="Categoría 1")
        cat2 = expense_category_factory(user, name="Categoría 2")

        budget1 = Budget.objects.create(
            user=user, category=cat1, month=today.month, year=today.year, amount=Decimal("5000.00")
        )

        budget2 = Budget.objects.create(
            user=user, category=cat2, month=today.month, year=today.year, amount=Decimal("3000.00")
        )

        assert budget1.pk is not None
        assert budget2.pk is not None

    def test_same_category_month_different_user_allowed(
        self, user, other_user, expense_category_factory
    ):
        """Verifica que mismo mes/categoría con diferente usuario sea permitido."""
        today = timezone.now().date()

        cat1 = expense_category_factory(user, name="Alimentación")
        cat2 = expense_category_factory(other_user, name="Alimentación")

        budget1 = Budget.objects.create(
            user=user, category=cat1, month=today.month, year=today.year, amount=Decimal("5000.00")
        )

        budget2 = Budget.objects.create(
            user=other_user,
            category=cat2,
            month=today.month,
            year=today.year,
            amount=Decimal("8000.00"),
        )

        assert budget1.pk is not None
        assert budget2.pk is not None


@pytest.mark.django_db
class TestCopyFromPreviousMonth:
    """Tests para el método copy_from_previous_month."""

    def test_copy_budgets_from_previous_month(self, user, expense_category_factory):
        """Verifica que se copian los presupuestos del mes anterior."""
        # Crear categorías
        cat1 = expense_category_factory(user, name="Comida")
        cat2 = expense_category_factory(user, name="Transporte")

        # Crear presupuestos en mes anterior (Diciembre 2025)
        Budget.objects.create(
            user=user,
            category=cat1,
            month=12,
            year=2025,
            amount=Decimal("10000.00"),
            alert_threshold=80,
        )
        Budget.objects.create(
            user=user,
            category=cat2,
            month=12,
            year=2025,
            amount=Decimal("5000.00"),
            alert_threshold=70,
        )

        # Copiar a Enero 2026
        created = Budget.copy_from_previous_month(user, target_month=1, target_year=2026)

        assert len(created) == 2

        # Verificar que se crearon correctamente
        new_budgets = Budget.objects.filter(user=user, month=1, year=2026)
        assert new_budgets.count() == 2

        # Verificar montos y umbrales copiados
        budget_comida = new_budgets.get(category=cat1)
        assert budget_comida.amount == Decimal("10000.00")
        assert budget_comida.alert_threshold == 80
        assert "Copiado de" in budget_comida.notes

        budget_transporte = new_budgets.get(category=cat2)
        assert budget_transporte.amount == Decimal("5000.00")
        assert budget_transporte.alert_threshold == 70

    def test_copy_skips_existing_budgets(self, user, expense_category_factory):
        """Verifica que no duplica presupuestos existentes."""
        cat1 = expense_category_factory(user, name="Comida")
        cat2 = expense_category_factory(user, name="Transporte")

        # Crear presupuestos en mes anterior
        Budget.objects.create(
            user=user,
            category=cat1,
            month=12,
            year=2025,
            amount=Decimal("10000.00"),
        )
        Budget.objects.create(
            user=user,
            category=cat2,
            month=12,
            year=2025,
            amount=Decimal("5000.00"),
        )

        # Crear presupuesto existente en mes destino (cat1 ya existe)
        Budget.objects.create(
            user=user,
            category=cat1,
            month=1,
            year=2026,
            amount=Decimal("12000.00"),  # Monto diferente
        )

        # Copiar
        created = Budget.copy_from_previous_month(user, target_month=1, target_year=2026)

        # Solo debe crear 1 (cat2), no duplicar cat1
        assert len(created) == 1
        assert created[0].category == cat2

        # Verificar que cat1 mantiene su monto original
        budget_comida = Budget.objects.get(user=user, category=cat1, month=1, year=2026)
        assert budget_comida.amount == Decimal("12000.00")

    def test_copy_returns_empty_if_no_source_budgets(self, user):
        """Verifica que retorna lista vacía si no hay presupuestos en mes anterior."""
        created = Budget.copy_from_previous_month(user, target_month=1, target_year=2026)

        assert created == []

    def test_copy_returns_empty_if_all_exist(self, user, expense_category_factory):
        """Verifica que retorna lista vacía si todos los presupuestos ya existen."""
        cat1 = expense_category_factory(user, name="Comida")

        # Crear en mes anterior
        Budget.objects.create(
            user=user,
            category=cat1,
            month=12,
            year=2025,
            amount=Decimal("10000.00"),
        )

        # Crear en mes destino (ya existe)
        Budget.objects.create(
            user=user,
            category=cat1,
            month=1,
            year=2026,
            amount=Decimal("10000.00"),
        )

        created = Budget.copy_from_previous_month(user, target_month=1, target_year=2026)

        assert created == []

    def test_copy_handles_year_boundary(self, user, expense_category_factory):
        """Verifica que maneja correctamente el cambio de año (Enero -> Diciembre anterior)."""
        cat1 = expense_category_factory(user, name="Comida")

        # Crear presupuesto en Diciembre 2025
        Budget.objects.create(
            user=user,
            category=cat1,
            month=12,
            year=2025,
            amount=Decimal("10000.00"),
        )

        # Copiar a Enero 2026
        created = Budget.copy_from_previous_month(user, target_month=1, target_year=2026)

        assert len(created) == 1
        assert created[0].month == 1
        assert created[0].year == 2026

    def test_copy_handles_mid_year(self, user, expense_category_factory):
        """Verifica copia en meses intermedios del año."""
        cat1 = expense_category_factory(user, name="Comida")

        # Crear presupuesto en Mayo
        Budget.objects.create(
            user=user,
            category=cat1,
            month=5,
            year=2026,
            amount=Decimal("8000.00"),
        )

        # Copiar a Junio
        created = Budget.copy_from_previous_month(user, target_month=6, target_year=2026)

        assert len(created) == 1
        assert created[0].month == 6
        assert created[0].year == 2026

    def test_copy_does_not_affect_other_users(self, user, other_user, expense_category_factory):
        """Verifica que la copia no afecta a otros usuarios."""
        cat_user = expense_category_factory(user, name="Comida User")
        cat_other = expense_category_factory(other_user, name="Comida Other")

        # Crear presupuestos para ambos usuarios
        Budget.objects.create(
            user=user,
            category=cat_user,
            month=12,
            year=2025,
            amount=Decimal("10000.00"),
        )
        Budget.objects.create(
            user=other_user,
            category=cat_other,
            month=12,
            year=2025,
            amount=Decimal("8000.00"),
        )

        # Copiar solo para user
        created = Budget.copy_from_previous_month(user, target_month=1, target_year=2026)

        assert len(created) == 1
        assert created[0].user == user

        # Verificar que other_user no tiene presupuestos en Enero
        other_budgets = Budget.objects.filter(user=other_user, month=1, year=2026)
        assert other_budgets.count() == 0


@pytest.mark.django_db
class TestBudgetValidation:
    def test_amount_must_be_positive(self, user, expense_category, current_month, current_year):
        budget = Budget(
            user=user,
            category=expense_category,
            month=current_month,
            year=current_year,
            amount=Decimal("0.00"),
        )

        with pytest.raises(ValidationError) as exc:
            budget.full_clean()

        err = exc.value.message_dict["amount"]
        assert any("mayor a cero" in msg.lower() or "0.01" in msg for msg in err)

    def test_category_must_be_expense(self, user, income_category, current_month, current_year):
        budget = Budget(
            user=user,
            category=income_category,
            month=current_month,
            year=current_year,
            amount=Decimal("1000.00"),
        )

        with pytest.raises(ValidationError) as exc:
            budget.full_clean()

        err = exc.value.message_dict["category"]
        assert any("solo" in msg.lower() and "gasto" in msg.lower() for msg in err)


@pytest.mark.django_db
class TestBudgetPeriod:
    def test_month_name(self, budget):
        # No atarse a idioma exacto, pero sí a que no esté vacío
        assert isinstance(budget.month_name, str)
        assert budget.month_name.strip() != ""

    def test_period_display(self, budget):
        assert str(budget.year) in budget.period_display
        assert budget.month_name in budget.period_display


@pytest.mark.django_db
class TestBudgetFormatting:
    def test_formatted_remaining_negative_shows_minus(
        self, user, expense_category, budget_factory, expense_factory
    ):
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("1000.00")
        )

        expense_factory(user, expense_category, amount=Decimal("1500.00"), date=today)

        assert budget.remaining_amount < 0
        assert budget.formatted_remaining.startswith("-$") or budget.formatted_remaining.startswith(
            "-$ "
        )


@pytest.mark.django_db
class TestBudgetStatusClass:
    def test_status_class_ok(self, budget):
        assert budget.status_class == "success"

    def test_status_class_warning(self, user, expense_category, budget_factory, expense_factory):
        today = timezone.now().date()
        budget = budget_factory(
            user,
            expense_category,
            month=today.month,
            year=today.year,
            amount=Decimal("10000.00"),
            alert_threshold=80,
        )
        expense_factory(user, expense_category, amount=Decimal("8500.00"), date=today)
        assert budget.status == "warning"
        assert budget.status_class == "warning"

    def test_status_class_over(self, user, expense_category, budget_factory, expense_factory):
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )
        expense_factory(user, expense_category, amount=Decimal("12000.00"), date=today)
        assert budget.status == "over"
        assert budget.status_class == "danger"


@pytest.mark.django_db
class TestBudgetClassmethods:
    def test_get_user_budgets_no_filters(
        self, user, other_user, expense_category, expense_category_factory, budget_factory
    ):
        b1 = budget_factory(user, expense_category, month=1, year=2026)
        other_cat = expense_category_factory(other_user, name="Other")
        b2 = budget_factory(other_user, other_cat, month=1, year=2026)

        qs = Budget.get_user_budgets(user)
        assert b1 in qs
        assert b2 not in qs

    def test_get_user_budgets_filter_year(self, user, expense_category, budget_factory):
        b2026 = budget_factory(user, expense_category, month=1, year=2026)
        b2025 = budget_factory(user, expense_category, month=12, year=2025)

        qs = Budget.get_user_budgets(user, year=2026)
        assert b2026 in qs
        assert b2025 not in qs

    def test_get_user_budgets_filter_month_year(self, user, expense_category, budget_factory):
        b_jan = budget_factory(user, expense_category, month=1, year=2026)
        b_feb = budget_factory(user, expense_category, month=2, year=2026)

        qs = Budget.get_user_budgets(user, month=1, year=2026)
        assert b_jan in qs
        assert b_feb not in qs

    def test_get_current_month_budgets(self, user, expense_category, budget_factory):
        today = timezone.now().date()
        b = budget_factory(user, expense_category, month=today.month, year=today.year)
        qs = Budget.get_current_month_budgets(user)
        assert b in qs


@pytest.mark.django_db
class TestBudgetMonthlySummary:
    def test_get_monthly_summary(self, user, expense_category_factory, expense_factory):
        today = timezone.now().date()
        cat1 = expense_category_factory(user, name="C1")
        cat2 = expense_category_factory(user, name="C2")

        Budget.objects.create(
            user=user,
            category=cat1,
            month=today.month,
            year=today.year,
            amount=Decimal("10000.00"),
            alert_threshold=80,
        )
        Budget.objects.create(
            user=user,
            category=cat2,
            month=today.month,
            year=today.year,
            amount=Decimal("5000.00"),
            alert_threshold=80,
        )

        # b1 queda warning (85%)
        expense_factory(user, cat1, amount=Decimal("8500.00"), date=today)
        # b2 queda over (120%)
        expense_factory(user, cat2, amount=Decimal("6000.00"), date=today)

        summary = Budget.get_monthly_summary(user, month=today.month, year=today.year)

        assert summary["total_budgeted"] == Decimal("15000.00")
        assert summary["total_spent"] == Decimal("14500.00")
        assert summary["total_remaining"] == Decimal("500.00")
        assert summary["budget_count"] == 2
        assert summary["warning_count"] == 1
        assert summary["over_budget_count"] == 1
        assert summary["overall_percentage"] == round(
            (Decimal("14500.00") / Decimal("15000.00") * 100), 1
        )

    def test_get_monthly_summary_zero_budgeted_returns_zero_percentage(self, user):
        summary = Budget.get_monthly_summary(user, month=1, year=2030)
        assert summary["total_budgeted"] == 0
        assert summary["overall_percentage"] == 0
        assert summary["budget_count"] == 0


@pytest.mark.django_db
class TestBudgetSpentAnnotatedBranch:
    def test_spent_amount_uses_annotated_value(self, user, expense_category, budget_factory):
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )

        # Simular annotación del queryset
        budget._spent_annotated = Decimal("1234.00")

        assert budget.spent_amount == Decimal("1234.00")

    def test_spent_amount_annotated_none_returns_zero(self, user, expense_category, budget_factory):
        today = timezone.now().date()
        budget = budget_factory(
            user, expense_category, month=today.month, year=today.year, amount=Decimal("10000.00")
        )
        budget._spent_annotated = None
        assert budget.spent_amount == Decimal("0")
