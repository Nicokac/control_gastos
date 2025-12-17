"""
Vistas para gestión de presupuestos.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


# Create your views here.
class BudgetListView(LoginRequiredMixin, TemplateView):
    template_name = 'budgets/budget_list.html'
