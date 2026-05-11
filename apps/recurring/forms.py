"""Formularios para gastos recurrentes."""

from django import forms

from apps.categories.models import Category
from apps.core.constants import CategoryType

from .models import RecurringExpense


class RecurringExpenseForm(forms.ModelForm):
    class Meta:
        model = RecurringExpense
        fields = ["name", "category", "due_day", "notes", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "due_day": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 31}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Opcional"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.get_user_categories(user, CategoryType.EXPENSE)
        self.fields["category"].widget.attrs["class"] = "form-select"
        self.fields["category"].empty_label = "Seleccioná una categoría"
