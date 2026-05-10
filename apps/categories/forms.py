"""
Formularios para categorías.
"""

from django import forms

from apps.core.constants import (
    CATEGORY_COLOR_CHOICES,
    CATEGORY_ICON_CHOICES,
    DEFAULT_CATEGORY_COLOR,
)

from .models import Category


class CategoryForm(forms.ModelForm):
    """Formulario para crear/editar categorías de usuario."""

    color = forms.ChoiceField(
        choices=CATEGORY_COLOR_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "color-radio"}),
        initial=DEFAULT_CATEGORY_COLOR,
        required=False,
    )

    class Meta:
        model = Category
        fields = ["name", "type", "parent", "icon", "color"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre de la categoría"}
            ),
            "type": forms.Select(attrs={"class": "form-select"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "icon": forms.RadioSelect(
                attrs={"class": "icon-radio"},
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Inicializa el formulario con el usuario.
        Args:
            user: Usuario que crea la categoría
        """
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["icon"].choices = [("", "Sin ícono")] + CATEGORY_ICON_CHOICES
        self.fields["icon"].required = False
        self.fields["parent"].required = False
        self.fields["parent"].empty_label = "-- Sin grupo (crear grupo nuevo) --"
        if user:
            self.fields["parent"].queryset = Category.get_groups(user)
        # Pre-cargar color desde instancia (ChoiceField no se vincula automáticamente)
        if self.instance.pk and self.instance.color:
            self.fields["color"].initial = self.instance.color

    def clean(self):
        cleaned = super().clean()

        name = cleaned.get("name")
        if isinstance(name, str):
            cleaned["name"] = name.strip()

        icon = cleaned.get("icon")
        if icon is not None and isinstance(icon, str) and not icon.strip():
            cleaned["icon"] = ""

        color = cleaned.get("color")
        if not color:
            cleaned["color"] = DEFAULT_CATEGORY_COLOR

        return cleaned

    def clean_name(self):
        """Válida que el nombre no esté duplicado para el usuario."""
        name = self.cleaned_data.get("name")
        if isinstance(name, str):
            name = name.strip()

        category_type = self.cleaned_data.get("type") or self.instance.type
        if not name:
            return name

        # Si no pasaron user (tests/edit), usar el user de la instancia
        effective_user = self.user or getattr(self.instance, "user", None)

        # Si es creación y no hay user, que falle limpio (evita llegar al model.clean)
        if self.instance.pk is None and effective_user is None:
            raise forms.ValidationError("Debés estar autenticado para crear categorías.")

        # Duplicados del usuario (solo si sabemos qué usuario es)
        if effective_user is not None:
            queryset = Category.objects.filter(
                name__iexact=name, user=effective_user, type=category_type
            )

            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise forms.ValidationError(
                    "Ya tenés una categoría con este nombre para este tipo."
                )

        # Duplicados en categorías del sistema
        if Category.objects.filter(name__iexact=name, is_system=True, type=category_type).exists():
            raise forms.ValidationError("Ya existe una categoría del sistema con este nombre.")

        return name

    def save(self, commit=True):
        """Guarda la categoría asignando el usuario."""
        instance = super().save(commit=False)

        # Siempre user-category desde este form
        instance.is_system = False

        # Solo asignar user si fue provisto (evita pisar user en edits y permite commit=False en tests)
        if self.user is not None:
            instance.user = self.user

        if commit:
            instance.save()

        return instance
