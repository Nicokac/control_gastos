"""
Formularios para gastos.
"""

from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import Currency, ExpenseType, PaymentMethod
from apps.core.forms import BaseFilterForm
from apps.savings.models import Saving, SavingStatus

from .models import Expense


class ExpenseForm(forms.ModelForm):
    """
    Formulario optimizado para registro rápido de gastos.

    Principios UX aplicados:
    - Campo de monto grande y destacado (Fitts)
    - Fecha default = hoy (Tesler)
    - Campos opcionales separados (Carga Cognitiva)
    """

    class Meta:
        model = Expense
        fields = [
            "date",
            "category",
            "amount",
            "currency",
            "exchange_rate",
            "description",
            "payment_method",
            "expense_type",
            "saving",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg text-end",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0.01",
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
                    "placeholder": "Ej: Supermercado, Nafta, Netflix...",
                }
            ),
            "payment_method": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "expense_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "exchange_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.0001",
                    "min": "0.0001",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Inicializa el formulario.

        Args:
            :param user: Description
        """
        self.user = user
        super().__init__(*args, **kwargs)

        # Configurar categorías del usuario (solo tipo EXPENSE)
        if user:
            self.fields["category"] = forms.ModelChoiceField(
                queryset=Category.get_expense_categories(user),
                widget=forms.RadioSelect(
                    attrs={
                        "class": "category-radio",
                    }
                ),
                empty_label=None,
                required=True,
            )

            # Configurar campo de ahorro (solo activos del usuario)
            self.fields["saving"] = forms.ModelChoiceField(
                queryset=Saving.objects.filter(user=user, status=SavingStatus.ACTIVE),
                required=False,
                empty_label="-- No vincular a ahorro --",
                widget=forms.Select(
                    attrs={
                        "class": "form-select",
                    }
                ),
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
        self.fields["payment_method"].required = False
        self.fields["expense_type"].required = False
        self.fields["exchange_rate"].required = False

        # Agregar opción vacía a selects opcionales
        self.fields["payment_method"].choices = [("", "-- Opcional --")] + list(
            PaymentMethod.choices
        )
        self.fields["expense_type"].choices = [("", "-- Opcional --")] + list(ExpenseType.choices)

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

    def clean(self):
        """Validaciones adicionales."""
        cleaned_data = super().clean()

        # Validar que la categoría pertenezca al usuario o sea del sistema
        category = cleaned_data.get("category")
        if category and self.user:
            if not category.is_system and category.user != self.user:
                raise forms.ValidationError({"category": "Categoría no válida."})

            # Validar que la categoría sea de tipo EXPENSE
            from apps.core.constants import CategoryType

            if category.type != CategoryType.EXPENSE:
                raise forms.ValidationError({"category": "La categoría debe ser de tipo Gasto."})

        return cleaned_data

    def save(self, commit=True):
        """Guarda el gasto asignando el usuario."""
        instance = super().save(commit=False)
        instance.user = self.user

        if commit:
            instance.save()

        return instance


class ExpenseFilterForm(BaseFilterForm):
    """Formulario para filtrar gastos."""

    def get_category_queryset(self, user):
        return Category.get_expense_categories(user)
