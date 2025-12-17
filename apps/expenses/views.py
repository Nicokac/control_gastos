"""Vistas para gestión de gastos."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


# Create your views here.
class ExpenseListView(LoginRequiredMixin, TemplateView):
    """Lista de gastos - Placeholder."""
    template_name = 'expenses/expense_list.html'

class ExpenseCreateView(LoginRequiredMixin, TemplateView):
    """Crear gasto - Placeholder."""
    template_name = 'expenses/expense_form.html'
