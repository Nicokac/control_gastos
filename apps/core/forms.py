"""
Formularios base reutilizables.
"""

from django import forms

from apps.categories.models import Category


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
