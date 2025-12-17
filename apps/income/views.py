"""Vistas para gestión de ingresos."""


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


# Create your views here.
class IncomeListView(LoginRequiredMixin, TemplateView):
    template_name = 'income/income_list.html'

class IncomeCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'income/income_form.html'
