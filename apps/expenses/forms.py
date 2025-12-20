"""
Formularios para gastos.
"""

from django import forms 
from django.utils import timezone
from decimal import Decimal

from .models import Expense
from apps.categories.models import Category
from apps.core.constants import Currency, PaymentMethod, ExpenseType, CategoryType


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
            'amount',
            'currency',
            'category',
            'date',
            'description',
            'payment_method',
            'expense_type',
            'exchange_rate',
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'autofocus': True,
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Supermercado, Nafta, Netflix...',
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select',
            }),
            'expense_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0.0001',
            }),
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
            self.fields['category'] = forms.ModelChoiceField(
                queryset=Category.get_expense_categories(user),
                widget=forms.RadioSelect(attrs={
                    'class': 'category-radio',
                }),
                empty_label=None,
                required=True,
            )

        # Fecha default = hoy
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()

        # Moneda default del usuario
        if user and not self.instance.pk:
            self.fields['currency'].initial = user.default_currency

        # Exchange rate default
        if not self.instance.pk:
            self.fields['exchange_rate'].initial = Decimal('1.0000')

        # Hacer campos opcionales explícitamente no requeridos
        self.fields['payment_method'].required = False
        self.fields['expense_type'].required = False
        self.fields['exchange_rate'].required = False

        # Agregar opción vacía a selects opcionales
        self.fields['payment_method'].choices = [('', '-- Opcional --')] + list(PaymentMethod.choices)
        self.fields['expense_type'].choices = [('', '-- Opcional --')] + list(ExpenseType.choices)

    def clean_amount(self):
        """Valida que el monto sea positivo."""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero.')
        return amount
    
    def clean_exchange_rate(self):
        """Valida y setea exchange_rate según la moneda."""
        exchange_rate = self.cleaned_data.get('exchange_rate')
        currency = self.cleaned_data.get('currency')

        # Si es ARS, exchange_rate siempre es 1
        if currency == Currency.ARS:
            return Decimal('1.0000')
        
        # Si es USD y no hay exchange_rate, error
        if currency == Currency.USD and (not exchange_rate or exchange_rate <= 0):
            raise forms.ValidationError('Ingresá la cotización del dólar.')
        
        return exchange_rate or Decimal('1.0000')
    
    def clean(self):
        """Validaciones adicionales."""
        cleaned_data = super().clean()

        # Validar que la categoría pertenezca al usuario o sea del sistema
        category = cleaned_data.get('category')
        if category and self.user:
            if not category.is_system and category.user != self.user:
                raise forms.ValidationError({
                    'category': 'Categoría no válida.'
                })
            
    def save(self, commit=True):
        """Guarda el gasto asignando el usuario."""
        instance = super().save(commit=False)
        instance.user = self.user

        if commit:
            instance.save()

        return instance
    
class ExpenseFilterForm(forms.Form):
    """Formulario para filtrar gastos."""

    month = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'forms-select form-select-sm'})
    )
    year = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Generar choices de meses
        from apps.core.utils import get_months_choices, get_years_choices
        self.fields['month'].choices = [('', 'Todos los meses')] + get_months_choices()
        self.fields['year'].choices = [('', 'Todos los años')] + get_years_choices

        # Categorías del usuario
        if user:
            self.fields['category'].queryset = Category.get_expense_categories(user)
            self.fields['categoty'].empty_label = 'Todos las categorías'

        