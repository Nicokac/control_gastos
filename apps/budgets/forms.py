"""
Formularios para presupuestos.
"""

from django import forms
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.core.forms import BaseFilterForm
from apps.core.utils import get_months_choices, get_years_choices

from .models import Budget


class BudgetForm(forms.ModelForm):
    """Formulario para crear/editar presupuestos."""

    class Meta:
        model = Budget
        fields = [
            "category",
            "month",
            "year",
            "amount",
            "alert_threshold",
            "notes",
        ]
        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg text-end",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "alert_threshold": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "100",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Notas opcionales...",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        # Configurar categorías del usuario (solo tipo EXPENSE)
        if user:
            self.fields["category"] = forms.ModelChoiceField(
                queryset=Category.get_expense_categories(user),
                widget=forms.Select(attrs={"class": "form-select"}),
                empty_label="-- Seleccionar categoría --",
                required=True,
            )

        # Configurar mes
        self.fields["month"] = forms.ChoiceField(
            choices=get_months_choices(),
            widget=forms.Select(attrs={"class": "form-select"}),
            required=True,
        )

        # Configurar año
        self.fields["year"] = forms.ChoiceField(
            choices=get_years_choices(),
            widget=forms.Select(attrs={"class": "form-select"}),
            required=True,
        )

        # Defaults para nuevo presupuesto
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields["month"].initial = today.month
            self.fields["year"].initial = today.year
            self.fields["alert_threshold"].initial = 80

    def clean_amount(self):
        """Valida que el monto sea positivo."""
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        return amount

    def clean_alert_threshold(self):
        """Valida que el umbral esté entre 1 y 100."""
        threshold = self.cleaned_data.get("alert_threshold")
        # 🔧 SIM102: combinar if anidados en una sola condición
        if threshold is not None and not 1 <= threshold <= 100:
            raise forms.ValidationError("El umbral debe estar entre 1 y 100.")
        return threshold

    def clean(self):
        """Validaciones adicionales."""
        cleaned_data = super().clean()

        category = cleaned_data.get("category")
        month = cleaned_data.get("month")
        year = cleaned_data.get("year")

        # Validar que la categoría sea de tipo EXPENSE
        # 🔧 SIM102: combinar if anidados
        if category and category.type != CategoryType.EXPENSE:
            raise forms.ValidationError(
                {"category": "Solo se pueden crear presupuestos para categorías de gasto."}
            )

        # Validar que no exista otro presupuesto para la misma categoría/mes/año
        if category and month and year and self.user:
            # Convertir a int si vienen como string
            try:
                month = int(month)
                year = int(year)
            except (ValueError, TypeError):
                return cleaned_data

            existing = Budget.objects.filter(
                user=self.user, category=category, month=month, year=year, is_active=True
            )

            # Excluir el presupuesto actual si estamos editando
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                existing_budget = existing.first()
                from apps.core.utils import get_month_name

                month_name = get_month_name(month)
                raise forms.ValidationError(
                    {
                        "category": (
                            f'Ya existe un presupuesto para "{category.name}" '
                            f"en {month_name} {year} "
                            f"(Monto: ${existing_budget.amount:,.2f})."
                        )
                    }
                )

        return cleaned_data

    def save(self, commit=True):
        """Guarda el presupuesto asignando el usuario."""
        instance = super().save(commit=False)
        instance.user = self.user

        if commit:
            instance.save()

        return instance


class BudgetFilterForm(BaseFilterForm):
    """Formulario para filtrar presupuestos."""

    def get_category_queryset(self, user):
        return Category.get_expense_categories(user)


class CopyBudgetsForm(forms.Form):
    """Formulario para copiar presupuestos del mes anterior."""

    target_month = forms.ChoiceField(
        choices=[], widget=forms.Select(attrs={"class": "form-select"}), label="Mes destino"
    )
    target_year = forms.ChoiceField(
        choices=[], widget=forms.Select(attrs={"class": "form-select"}), label="Año destino"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["target_month"].choices = get_months_choices()
        self.fields["target_year"].choices = get_years_choices()

        # Default al mes actual
        today = timezone.now().date()
        self.fields["target_month"].initial = today.month
        self.fields["target_year"].initial = today.year
