"""
Formularios base reutilizables.
"""

from decimal import Decimal

from django import forms

from apps.categories.models import Category
from apps.core.constants import Currency


class CurrencyFormMixin:
    """
    Mixin con validaciones comunes para formularios con moneda.

    Uso:
        class ExpenseForm(CurrencyFormMixin, forms.ModelForm):
            ...
    """

    def clean_amount(self):
        """Valida que el monto sea positivo."""
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return amount

    def clean_exchange_rate(self):
        """Valida y setea exchange_rate según la moneda."""
        exchange_rate = self.cleaned_data.get("exchange_rate")
        currency = self.cleaned_data.get("currency")

        # Si es ARS, exchange_rate siempre es 1
        if currency == Currency.ARS:
            return Decimal("1.0000")

        # Si es USD, validar exchange_rate
        if currency == Currency.USD:
            if not exchange_rate:
                raise forms.ValidationError("Ingresá la cotización del dólar.")
            if exchange_rate <= 0:
                raise forms.ValidationError("La cotización debe ser mayor a cero.")
            return exchange_rate

        return Decimal("1.0000")


class BaseFilterForm(forms.Form):
    """
    Form base para filtros de mes/año/categoría.

    Uso:
        class ExpenseFilterForm(BaseFilterForm):
            def get_category_queryset(self, user):
                return Category.get_expense_categories(user)
    """

    month = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    year = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    def __init__(self, *args, user=None, include_empty_choice=True, **kwargs):
        super().__init__(*args, **kwargs)

        from apps.core.utils import get_months_choices, get_years_choices

        # Configurar choices de meses y años
        if include_empty_choice:
            self.fields["month"].choices = [("", "Todos los meses")] + get_months_choices()
            self.fields["year"].choices = [("", "Todos los años")] + get_years_choices()
        else:
            self.fields["month"].choices = get_months_choices()
            self.fields["year"].choices = get_years_choices()

        # Configurar categorías del usuario
        if user:
            self.fields["category"].queryset = self.get_category_queryset(user)
            self.fields["category"].empty_label = "Todas las categorías"

    def get_category_queryset(self, user):
        """
        Override en subclases para filtrar categorías.

        Returns:
            QuerySet de categorías filtradas para el usuario.
        """
        raise NotImplementedError("Subclases deben implementar get_category_queryset()")
