"""Formularios para gastos recurrentes."""

from django import forms

from apps.categories.models import Category
from apps.core.constants import CategoryType

from .models import RecurringExpense


class RecurringExpenseForm(forms.ModelForm):
    class Meta:
        model = RecurringExpense
        fields = [
            "name",
            "category",
            "due_day",
            "notes",
            "is_active",
            "total_installments",
            "starting_installment",
            "start_date",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "due_day": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 31}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Opcional"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "total_installments": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "placeholder": "Ej: 12"}
            ),
            "starting_installment": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "placeholder": "Ej: 4"}
            ),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.get_user_categories(user, CategoryType.EXPENSE)
        self.fields["category"].widget.attrs["class"] = "form-select"
        self.fields["category"].empty_label = "Seleccioná una categoría"
        self.fields["total_installments"].required = False
        self.fields["starting_installment"].required = False
        self.fields["start_date"].required = False

    def clean(self):
        cleaned_data = super().clean()
        installments = cleaned_data.get("total_installments")
        start_date = cleaned_data.get("start_date")
        starting = cleaned_data.get("starting_installment")
        if installments and not start_date:
            self.add_error(
                "start_date", "Indicá el mes de inicio para calcular el progreso de cuotas."
            )
        if start_date and not installments:
            self.add_error("total_installments", "Indicá la cantidad total de cuotas.")
        if starting and not installments:
            self.add_error("starting_installment", "Indicá primero la cantidad total de cuotas.")
        if starting and installments and starting >= installments:
            self.add_error(
                "starting_installment",
                f"La cuota de inicio debe ser menor que el total ({installments}).",
            )
        return cleaned_data
