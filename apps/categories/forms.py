"""
Formularios para categorías.
"""

from django import forms 
from .models import Category
from apps.core.constants import CategoryType

class CategoryForm(forms.ModelForm):
    """Formulario para crear/editar categorías de usuario."""

    class Meta:
        model = Category
        fields = ['name', 'type', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'bi-cart (opcional)'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#6c757d'
            }),
        }

    def __init__(self, *args, user=None, **kwars):
        """
        Inicializa el formulario con el usuario.
        
        Args:
            user: Usuario que crea la categoría
        """
        self.user = user
        super().__init__(*args, **kwars)

    def clean_name(self):
        """Válida que el nombre no esté duplicado para el usuario."""
        name = self.cleaned_data.get('name')
        category_type = self.cleaned_data.get('type') or self.instance.type

        if not name:
            return name
        
        # Verificar duplicados en categorías del usuario.
        queryset = Category.objects.filter(
            name__iexact=name,
            user=self.user,
            type=category_type
        )

        # Excluir la instancia actual si estamos editando
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                'Ya tenés una categoría con este nombre para este tipo.'
            )
        
        # Verificar que no coincida categorías del sistema
        if Category.objects.filter(
            name__iexact=name,
            is_system=True,
            type=category_type
        ).exists():
            raise forms.ValidationError(
                'Ya existe una categoría del sistema con este nombre.'
            )
        
        return name
    
    def save(self, commit=True):
        """Guarda la categoría asignando el usuario."""
        instance = super().save(commit=False)
        instance.user = self.user
        instance.is_system = False

        if commit:
            instance.save()

        return instance

