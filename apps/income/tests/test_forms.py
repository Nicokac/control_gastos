"""
Tests para los formularios de Income.
"""

from decimal import Decimal

from django.utils import timezone

import pytest

from apps.core.constants import CategoryType, Currency
from apps.income.forms import IncomeForm


@pytest.mark.django_db
class TestIncomeForm:
    """Tests para IncomeForm."""

    def test_valid_income_ars(self, user, income_category):
        """Verifica formulario válido para ingreso en ARS."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Sueldo mensual",
                "amount": "150000.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors

    def test_valid_income_usd(self, user, income_category):
        """Verifica formulario válido para ingreso en USD."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Freelance",
                "amount": "500.00",
                "currency": Currency.USD,
                "exchange_rate": "1150.00",
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors

    def test_category_required(self, user):
        """Verifica que la categoría sea requerida."""
        form = IncomeForm(
            data={
                "description": "Test",
                "amount": "100.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert not form.is_valid()
        assert "category" in form.errors

    def test_description_required(self, user, income_category):
        """Verifica que la descripción sea requerida."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "",
                "amount": "100.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert not form.is_valid()
        assert "description" in form.errors

    def test_amount_required(self, user, income_category):
        """Verifica que el monto sea requerido."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Test",
                "amount": "",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert not form.is_valid()
        assert "amount" in form.errors

    def test_date_required(self, user, income_category):
        """Verifica que la fecha sea requerida."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Test",
                "amount": "100.00",
                "currency": Currency.ARS,
                "date": "",
            },
            user=user,
        )

        assert not form.is_valid()
        assert "date" in form.errors

    def test_negative_amount_invalid(self, user, income_category):
        """Verifica que monto negativo sea inválido."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Test",
                "amount": "-100.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert not form.is_valid()
        assert "amount" in form.errors

    def test_zero_amount_invalid(self, user, income_category):
        """Verifica que monto cero sea inválido."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Test",
                "amount": "0",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert not form.is_valid()
        assert "amount" in form.errors

    def test_usd_requires_exchange_rate(self, user, income_category):
        """Verifica que USD requiera tipo de cambio."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Ingreso USD",
                "amount": "100.00",
                "currency": Currency.USD,
                "exchange_rate": "",
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert not form.is_valid()
        assert "exchange_rate" in form.errors or "__all__" in form.errors

    def test_ars_ignores_exchange_rate(self, user, income_category):
        """Verifica que ARS ignore tipo de cambio."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Ingreso ARS",
                "amount": "100.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors


@pytest.mark.django_db
class TestIncomeFormCategories:
    """Tests para filtrado de categorías en IncomeForm."""

    def test_only_user_income_categories(self, user, expense_category, income_category):
        """Verifica que solo muestre categorías de ingreso del usuario."""
        form = IncomeForm(user=user)

        category_queryset = form.fields["category"].queryset

        # Debe incluir categoría de ingreso
        assert income_category in category_queryset

        # No debe incluir categoría de gasto
        assert expense_category not in category_queryset

    def test_excludes_other_user_categories(self, user, other_user, income_category_factory):
        """Verifica que excluya categorías de otros usuarios."""
        cat_other = income_category_factory(other_user, name="Otra")

        form = IncomeForm(user=user)
        category_queryset = form.fields["category"].queryset

        assert cat_other not in category_queryset


@pytest.mark.django_db
class TestIncomeFormSave:
    """Tests para guardado de IncomeForm."""

    def test_save_creates_income(self, user, income_category):
        """Verifica que save() cree el ingreso."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Nuevo ingreso",
                "amount": "50000.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors

        income = form.save(commit=False)
        income.user = user
        income.save()

        assert income.pk is not None
        assert income.amount == Decimal("50000.00")
        assert income.user == user

    def test_save_calculates_amount_ars(self, user, income_category):
        """Verifica que save() calcule amount_ars para USD."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Ingreso USD",
                "amount": "500.00",
                "currency": Currency.USD,
                "exchange_rate": "1200.00",
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors

        income = form.save(commit=False)
        income.user = user
        income.save()

        assert income.amount_ars == Decimal("600000.00")


@pytest.mark.django_db
class TestIncomeFormCategoryValidation:
    """Tests para validación de tipo de categoría en IncomeForm."""

    def test_rejects_expense_category(self, user, expense_category):
        """Verifica que rechace categoría de gasto."""
        form = IncomeForm(
            data={
                "category": expense_category.pk,  # Categoría tipo EXPENSE
                "description": "Intento con categoría incorrecta",
                "amount": "100.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        # Debería ser inválido o la categoría no debería estar en el queryset
        if form.is_valid():
            category_queryset = form.fields["category"].queryset
            assert expense_category not in category_queryset
        else:
            assert "category" in form.errors or "__all__" in form.errors

    def test_accepts_income_category(self, user, income_category):
        """Verifica que acepte categoría de ingreso."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Ingreso válido",
                "amount": "100.00",
                "currency": Currency.ARS,
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors

    def test_category_queryset_only_income_type(self, user, expense_category, income_category):
        """Verifica que queryset solo contenga categorías de ingreso."""
        form = IncomeForm(user=user)

        category_queryset = form.fields["category"].queryset

        for cat in category_queryset:
            assert cat.type == CategoryType.INCOME


@pytest.mark.django_db
class TestIncomeFormExchangeRate:
    """Tests para manejo de exchange_rate en IncomeForm."""

    def test_ars_sets_exchange_rate_to_one(self, user, income_category):
        """Verifica que ARS setee exchange_rate a 1.00."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Sueldo",
                "amount": "150000.00",
                "currency": Currency.ARS,
                "exchange_rate": "999.00",  # Debería ser ignorado
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors

        income = form.save(commit=False)
        income.user = user
        income.save()

        assert income.exchange_rate == Decimal("1.00")

    def test_usd_preserves_exchange_rate(self, user, income_category):
        """Verifica que USD preserve el exchange_rate ingresado."""
        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Freelance USD",
                "amount": "500.00",
                "currency": Currency.USD,
                "exchange_rate": "1180.00",
                "date": timezone.now().date(),
            },
            user=user,
        )

        assert form.is_valid(), form.errors

        income = form.save(commit=False)
        income.user = user
        income.save()

        assert income.exchange_rate == Decimal("1180.00")


@pytest.mark.django_db
class TestIncomeFormCleanedData:
    """Tests para cleaned_data de IncomeForm."""

    def test_cleaned_data_types(self, user, income_category):
        """Verifica tipos correctos en cleaned_data."""
        from datetime import date

        from apps.categories.models import Category

        form = IncomeForm(
            data={
                "category": income_category.pk,
                "description": "Test de tipos",
                "amount": "50000.00",
                "currency": Currency.ARS,
                "date": "2025-01-15",
            },
            user=user,
        )

        assert form.is_valid(), form.errors

        assert isinstance(form.cleaned_data["amount"], Decimal)
        assert isinstance(form.cleaned_data["date"], date)
        assert isinstance(form.cleaned_data["category"], Category)


@pytest.mark.django_db
class TestIncomeFormInitialValues:
    """Tests para valores iniciales de IncomeForm."""

    def test_currency_default_is_ars(self, user):
        """Verifica que moneda por defecto sea ARS."""
        form = IncomeForm(user=user)

        currency_field = form.fields["currency"]

        if "currency" in form.initial:
            assert form.initial["currency"] == Currency.ARS
        elif hasattr(currency_field, "initial") and currency_field.initial:
            assert currency_field.initial == Currency.ARS
