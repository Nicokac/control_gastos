"""Vistas para dashboard y reportes."""


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


# Create your views here.
class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal."""

    template_name = 'reports/dashboard.html'

    def get_content_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dashboard'
        return context
