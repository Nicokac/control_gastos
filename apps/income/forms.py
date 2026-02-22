"""
Formularios para ingresos.
"""

from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import Currency
from apps.core.forms import BaseFilterForm

from .models import Income


class IncomeForm(forms.ModelForm):
    """Formulario optimizado para registro de ingresos."""

    class Meta:
        model = Income
        fields = [
            "amount",
            "currency",
            "category",
            "date",
            "description",
            "is_recurring",
            "exchange_rate",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg text-end",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0.01",
                    "autocomplete": "off",
                    "autofocus": True,
                }
            ),
            "currency": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Sueldo, Freelance, Alquiler...",
                }
            ),
            "is_recurring": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "exchange_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Inicializa el formulario.

        Args:
            user: Usuario actual (requerido)
        """
        self.user = user
        super().__init__(*args, **kwargs)

        # Configurar categorías del usuario (solo tipo Income)
        if user:
            self.fields["category"] = forms.ModelChoiceField(
                queryset=Category.get_income_categories(user),
                widget=forms.RadioSelect(
                    attrs={
                        "class": "category-radio",
                    }
                ),
                empty_label=None,
                required=True,
            )

        # Fecha default = hoy
        if not self.instance.pk:
            self.fields["date"].initial = timezone.now().date()

        # Moneda default del usuario
        if user and not self.instance.pk:
            self.fields["currency"].initial = user.default_currency

        # Exchange rate default
        if not self.instance.pk:
            self.fields["exchange_rate"].initial = Decimal("1.0000")

        # Hacer campos opcionales explícitamente no requeridos
        self.fields["is_recurring"].required = False
        self.fields["exchange_rate"].required = False

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
            # El campo puede venir vacío si estaba disabled
            if not exchange_rate:
                raise forms.ValidationError("Ingresá la cotización del dólar.")
            if exchange_rate <= 0:
                raise forms.ValidationError("La cotización debe ser mayor a cero.")
            return exchange_rate

        return Decimal("1.0000")

    def clean(self):  # 🔧 E SIM102
        """Validaciones adicionales."""
        cleaned_data = super().clean()

        # Validar que la categoría pertenezca al usuario o sea del sistema
        category = cleaned_data.get("category")
        if category and self.user and not category.is_system and category.user != self.user:
            raise forms.ValidationError({"category": "Categoría no válida."})

        return cleaned_data

    def save(self, commit=True):
        """Guarda el ingreso asignado el usuario."""
        instance = super().save(commit=False)
        instance.user = self.user

        if commit:
            instance.save()

        return instance


class IncomeFilterForm(BaseFilterForm):
    """Formulario para filtrar ingresos."""

    def get_category_queryset(self, user):
        return Category.get_income_categories(user)
