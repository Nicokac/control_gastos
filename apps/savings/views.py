"""
Vistas para gestión de ahorro.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

# Create your views here.
class SavingListView(LoginRequiredMixin, TemplateView):
    template_name = 'savings/saving_list.html'


class SavingCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'savings/saving_form.html'
