"""
Formularios para gastos.
"""

from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import ExpenseType, PaymentMethod
from apps.core.forms import BaseFilterForm, CurrencyFormMixin
from apps.savings.models import Saving, SavingStatus

from .models import Expense


class ExpenseForm(CurrencyFormMixin, forms.ModelForm):
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
        ]
        widgets = {
            "amount": forms.TextInput(
                attrs={
                    "class": "form-control form-control-lg text-end",
                    "placeholder": "0,00",
                    "inputmode": "decimal",
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
                widget=forms.Select(
                    attrs={
                        "class": "form-select",
                    }
                ),
                empty_label="-- Seleccionar categoría --",
                required=True,
            )

        # Quick Add: descripción opcional con fallback seguro
        self.fields["description"].required = False

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

        # Savings activas del usuario como destino opcional
        if user:
            self.fields["saving"] = forms.ModelChoiceField(
                queryset=Saving.objects.filter(user=user, status=SavingStatus.ACTIVE),
                required=False,
                empty_label="-- Sin destino de ahorro --",
                widget=forms.Select(attrs={"class": "form-select"}),
                label="Destino de ahorro",
            )
        else:
            self.fields["saving"] = forms.ModelChoiceField(
                queryset=Saving.objects.none(),
                required=False,
                widget=forms.Select(attrs={"class": "form-select"}),
                label="Destino de ahorro",
            )

        # Agregar opción vacía a selects opcionales
        self.fields["payment_method"].choices = [("", "-- Opcional --")] + list(
            PaymentMethod.choices
        )
        self.fields["expense_type"].choices = [("", "-- Opcional --")] + list(ExpenseType.choices)

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

    def clean_description(self):
        """Limpia el campo descripción."""
        description = (self.cleaned_data.get("description") or "").strip()
        return description

    def save(self, commit=True):
        """Guarda el gasto asignando el usuario y aplica depósito a meta si corresponde."""
        from django.db import transaction

        instance = super().save(commit=False)
        instance.user = self.user

        if commit:
            with transaction.atomic():
                instance.save()
                saving = self.cleaned_data.get("saving")
                if saving:
                    saving.add_deposit(
                        amount=instance.amount_ars,
                        description=f"Gasto vinculado: {instance.description or 'Sin descripción'}",
                    )

        return instance


class ExpenseFilterForm(BaseFilterForm):
    """Formulario para filtrar gastos."""

    payment_method = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    expense_type = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].choices = [("", "Todos los métodos")] + list(
            PaymentMethod.choices
        )
        self.fields["expense_type"].choices = [("", "Todos los tipos")] + list(ExpenseType.choices)

    def get_category_queryset(self, user):
        return Category.get_expense_categories(user)
