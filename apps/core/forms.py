"""
Formularios base reutilizables.
"""

from decimal import Decimal

from django import forms

from apps.categories.models import Category
from apps.core.constants import Currency


class ARSDecimalField(forms.DecimalField):
    """
    DecimalField que acepta formato argentino: "1.500,50" o "1500,50".

    Normaliza antes de la conversión: elimina puntos de miles y reemplaza
    la coma decimal por punto, para que Decimal() lo procese correctamente.
    """

    def to_python(self, value):
        if isinstance(value, str) and value.strip():
            v = value.strip()
            if "," in v:
                # Argentine format: "1.500,50" or "1500,50"
                # Strip thousands dots then swap decimal comma to dot
                v = v.replace(".", "").replace(",", ".")
            value = v
        return super().to_python(value)


class CurrencyFormMixin:
    """
    Mixin con validaciones comunes para formularios con moneda.

    Uso:
        class ExpenseForm(CurrencyFormMixin, forms.ModelForm):
            ...
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "amount" in self.fields:
            original = self.fields["amount"]
            # Preserve instance value before replacing the field
            instance_value = None
            if hasattr(self, "instance") and self.instance and self.instance.pk:
                instance_value = getattr(self.instance, "amount", None)
            new_field = ARSDecimalField(
                max_digits=getattr(original, "max_digits", 12),
                decimal_places=getattr(original, "decimal_places", 2),
                required=original.required,
                widget=original.widget,
                label=original.label,
                initial=instance_value if instance_value is not None else original.initial,
            )
            self.fields["amount"] = new_field

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


class FeedbackForm(forms.Form):
    """Formulario para que el usuario reporte bugs, mejoras u otros comentarios."""

    TIPO_CHOICES = [
        ("bug", "Bug / Falla"),
        ("mejora", "Sugerencia de mejora"),
        ("pregunta", "Pregunta"),
        ("otro", "Otro"),
    ]

    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        label="Tipo de reporte",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    mensaje = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describí el problema o sugerencia con el mayor detalle posible...",
                "required": True,
            }
        ),
        max_length=2000,
    )


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
