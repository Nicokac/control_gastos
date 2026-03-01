"""
Formularios para ahorro.
"""

from django import forms
from django.utils import timezone

from .models import MovementType, Saving, SavingMovement, SavingStatus

# Iconos disponibles para metas de ahorro
SAVING_ICONS = [
    ("bi-piggy-bank", "Alcancía"),
    ("bi-house", "Casa"),
    ("bi-car-front", "Auto"),
    ("bi-airplane", "Viaje"),
    ("bi-laptop", "Tecnología"),
    ("bi-mortarboard", "Educación"),
    ("bi-heart-pulse", "Salud"),
    ("bi-gift", "Regalo"),
    ("bi-tools", "Reparaciones"),
    ("bi-shield-check", "Emergencias"),
    ("bi-graph-up-arrow", "Inversión"),
    ("bi-cash-stack", "General"),
]

# Colores disponibles
SAVING_COLORS = [
    ("#17a2b8", "Cyan"),
    ("#28a745", "Verde"),
    ("#007bff", "Azul"),
    ("#6f42c1", "Púrpura"),
    ("#fd7e14", "Naranja"),
    ("#dc3545", "Rojo"),
    ("#ffc107", "Amarillo"),
    ("#20c997", "Teal"),
]


class SavingForm(forms.ModelForm):
    """Formulario para crear/editar metas de ahorro."""

    icon = forms.ChoiceField(
        choices=SAVING_ICONS,
        widget=forms.RadioSelect(attrs={"class": "icon-radio"}),
        initial="bi-piggy-bank",
    )

    color = forms.ChoiceField(
        choices=SAVING_COLORS,
        widget=forms.RadioSelect(attrs={"class": "color-radio"}),
        initial="#17a2b8",
    )

    class Meta:
        model = Saving
        fields = [
            "name",
            "description",
            "target_amount",
            "currency",
            "target_date",
            "icon",
            "color",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Vacaciones, Auto nuevo, Fondo de emergencia...",
                    "autofocus": True,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "Descripción opcional...",
                }
            ),
            "target_amount": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg text-end",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "currency": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "target_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        # Moneda default del usuario
        if user and not self.instance.pk:
            self.fields["currency"].initial = user.default_currency

    def clean_target_amount(self):
        """Valida que el monto objetivo sea positivo."""
        target_amount = self.cleaned_data.get("target_amount")
        if target_amount is not None and target_amount <= 0:
            raise forms.ValidationError("El monto objetivo debe ser mayor a cero.")
        return target_amount

    def clean_target_date(self):
        """Valida que la fecha objetivo sea futura (si se especifica)."""
        target_date = self.cleaned_data.get("target_date")
        if target_date and target_date < timezone.now().date():
            raise forms.ValidationError("La fecha objetivo debe ser futura.")
        return target_date

    def save(self, commit=True):
        """Guarda la meta asignando el usuario."""
        instance = super().save(commit=False)

        # Solo asignar user si fue provisto (evita pisar user en edits y permite commit=False en tests)
        if self.user is not None:
            instance.user = self.user

        if commit:
            instance.save()

        return instance


class SavingMovementForm(forms.ModelForm):
    """Formulario para agregar movimientos de ahorro."""

    class Meta:
        model = SavingMovement
        fields = ["type", "amount"]
        widgets = {
            "type": forms.RadioSelect(attrs={"class": "movement-type-radio"}),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-lg text-end",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0.01",
                    "autofocus": True,
                }
            ),
        }

    def __init__(self, *args, saving=None, **kwargs):
        self.saving = saving
        super().__init__(*args, **kwargs)

        # Default a depósito
        self.fields["type"].initial = MovementType.DEPOSIT

    def clean_amount(self):
        """Valida el monto según el tipo de movimiento."""
        amount = self.cleaned_data.get("amount")

        if amount is not None and amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")

        return amount

    def clean(self):
        """Validaciones adicionales."""
        cleaned_data = super().clean()

        movement_type = cleaned_data.get("type")
        amount = cleaned_data.get("amount")

        # Validar que hay suficiente saldo para retiro
        if (
            movement_type == MovementType.WITHDRAWAL
            and self.saving
            and amount
            and amount > self.saving.current_amount
        ):
            raise forms.ValidationError(
                {"amount": f"No hay suficiente saldo. Disponible: {self.saving.formatted_current}"}
            )

        return cleaned_data

    def save(self, commit=True):
        """Guarda el movimiento y actualiza la meta."""
        movement_type = self.cleaned_data.get("type")
        amount = self.cleaned_data.get("amount")

        if movement_type == MovementType.DEPOSIT:
            return self.saving.add_deposit(amount)
        else:
            return self.saving.add_withdrawal(amount)


class SavingFilterForm(forms.Form):
    """Formulario para filtrar metas de ahorro."""

    status = forms.ChoiceField(
        choices=[("", "Todos los estados")] + list(SavingStatus.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
