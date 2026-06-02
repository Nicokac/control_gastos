"""Formularios para gastos compartidos."""

from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.core.forms import CurrencyFormMixin

from .models import HouseholdMember, SharedExpense


class HouseholdMemberForm(forms.ModelForm):
    class Meta:
        model = HouseholdMember
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Nati, Mamá, Compañero..."}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        qs = HouseholdMember.objects.filter(user=self.user, name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya tenés un miembro con ese nombre.")
        return name

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance


class SharedExpenseForm(CurrencyFormMixin, forms.ModelForm):
    class Meta:
        model = SharedExpense
        fields = [
            "date",
            "category",
            "description",
            "amount",
            "currency",
            "exchange_rate",
            "paid_by",
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
            "currency": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "description": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Supermercado, Luz, Cena..."}
            ),
            "exchange_rate": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "inputmode": "decimal",
                    "placeholder": "0,00",
                    "autocomplete": "off",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user:
            self.fields["category"].queryset = Category.get_expense_categories(user)
            self.fields["paid_by"].queryset = HouseholdMember.objects.filter(user=user)

        self.fields["category"].widget.attrs["class"] = "form-select"
        self.fields["category"].empty_label = "-- Seleccionar categoría --"
        self.fields["paid_by"].widget.attrs["class"] = "form-select"
        self.fields["paid_by"].empty_label = "Yo"
        self.fields["paid_by"].required = False
        self.fields["exchange_rate"].required = False

        if not self.instance.pk:
            self.fields["date"].initial = timezone.localdate()
            self.fields["exchange_rate"].initial = Decimal("1.0000")
            if user:
                self.fields["currency"].initial = user.default_currency

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        if category and self.user:
            if not category.is_system and category.user != self.user:
                raise forms.ValidationError({"category": "Categoría no válida."})
            if category.type != CategoryType.EXPENSE:
                raise forms.ValidationError({"category": "La categoría debe ser de tipo Gasto."})
        paid_by = cleaned_data.get("paid_by")
        if paid_by and paid_by.user != self.user:
            raise forms.ValidationError({"paid_by": "El miembro no pertenece a tu hogar."})
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.user
        if commit:
            instance.save()
        return instance
