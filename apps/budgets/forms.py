"""
Formularios para presupuestos.
"""

from django import forms
from django.utils import timezone
from decimal import Decimal

from .models import Budget
from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.core.utils import get_months_choices, get_years_choices


class BudgetForm(forms.ModelForm):
    """Formulario para crear/editar presupuestos."""
    
    class Meta:
        model = Budget
        fields = [
            'category',
            'month',
            'year',
            'amount',
            'alert_threshold',
            'notes',
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg text-end',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
            }),
            'alert_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notas opcionales...',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Configurar categorías del usuario (solo tipo EXPENSE)
        if user:
            self.fields['category'] = forms.ModelChoiceField(
                queryset=Category.get_expense_categories(user),
                widget=forms.Select(attrs={'class': 'form-select'}),
                empty_label='-- Seleccionar categoría --',
                required=True,
            )
        
        # Configurar mes
        self.fields['month'] = forms.ChoiceField(
            choices=get_months_choices(),
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=True,
        )
        
        # Configurar año
        self.fields['year'] = forms.ChoiceField(
            choices=get_years_choices(),
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=True,
        )
        
        # Defaults para nuevo presupuesto
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['month'].initial = today.month
            self.fields['year'].initial = today.year
            self.fields['alert_threshold'].initial = 80

    def clean_amount(self):
        """Valida que el monto sea positivo."""
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero.')
        return amount

    def clean_alert_threshold(self):
        """Valida que el umbral esté entre 1 y 100."""
        threshold = self.cleaned_data.get('alert_threshold')
        if threshold is not None:
            if threshold < 1 or threshold > 100:
                raise forms.ValidationError('El umbral debe estar entre 1 y 100.')
        return threshold

    def clean(self):
        """Validaciones adicionales."""
        cleaned_data = super().clean()
        
        category = cleaned_data.get('category')
        month = cleaned_data.get('month')
        year = cleaned_data.get('year')
        
        # Validar que la categoría sea de tipo EXPENSE
        if category:
            if category.type != CategoryType.EXPENSE:
                raise forms.ValidationError({
                    'category': 'Solo se pueden crear presupuestos para categorías de gasto.'
                })
        
        # Validar que no exista otro presupuesto para la misma categoría/mes/año
        if category and month and year and self.user:
            existing = Budget.objects.filter(
                user=self.user,
                category=category,
                month=month,
                year=year,
                is_active=True
            )
            
            # Excluir el presupuesto actual si estamos editando
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError({
                    'category': f'Ya existe un presupuesto para {category.name} en este período.'
                })
        
        return cleaned_data

    def save(self, commit=True):
        """Guarda el presupuesto asignando el usuario."""
        instance = super().save(commit=False)
        instance.user = self.user
        
        if commit:
            instance.save()
        
        return instance


class BudgetFilterForm(forms.Form):
    """Formulario para filtrar presupuestos."""
    
    month = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
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
        self.fields['month'].choices = [('', 'Todos los meses')] + get_months_choices()
        self.fields['year'].choices = [('', 'Todos los años')] + get_years_choices()
        
        # Categorías del usuario (tipo EXPENSE)
        if user:
            self.fields['category'].queryset = Category.get_expense_categories(user)
            self.fields['category'].empty_label = 'Todas las categorías'


class CopyBudgetsForm(forms.Form):
    """Formulario para copiar presupuestos del mes anterior."""
    
    target_month = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mes destino'
    )
    target_year = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Año destino'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['target_month'].choices = get_months_choices()
        self.fields['target_year'].choices = get_years_choices()
        
        # Default al mes actual
        today = timezone.now().date()
        self.fields['target_month'].initial = today.month
        self.fields['target_year'].initial = today.year