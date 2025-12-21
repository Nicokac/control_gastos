"""
Vistas para gestión de ingresos.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils import timezone
from django.db.models import Sum

from .models import Income
from .forms import IncomeForm, IncomeFilterForm
from apps.categories.models import Category


# Create your views here.
class IncomeListView(LoginRequiredMixin, ListView):
    """List de ingresos jdel usuario con filtros."""

    model = Income
    template_name = 'income/income_list.html'
    context_name = 'income'
    paginate_by = 20

    def get_queryset(self):
        """Filtra ingresos del usuario actual."""
        queryset = Income.objects.filter(
            user=self.request.user
        ).select_related('category')

        # Aplicar filtros con validación
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        category = self.request.GET.get('category')

        try:
            if month:
                month = int(month)
                if 1 <= month <= 12:
                    queryset = queryset.filter(date__month=month)

            if year:
                year = int(year)
                if 1900 <= year <= 2100:
                    queryset = queryset.filter(date__year=year)

            if category:
                category = int(category)
                queryset = queryset.filter(category_id=category)
        except (ValueError, TypeError):
            pass # Ignorar parámetros inválidos

        return queryset
    
    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)

        # Formulario de filtros
        context['filter_form'] = IncomeFilterForm(
            data=self.request.GET or None,
            user=self.request.user
        )

        # Total del período filtrado
        queryset = self.get_queryset()
        context['total'] = queryset.aggregate(total=Sum('amount_ars'))['total'] or 0

        # Mes y año actual para defaults
        today = timezone.now().date()
        context['current_month'] = today.month
        context['current_year'] = today.year

        return context


class IncomeCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo ingreso."""

    model = Income
    form_class = IncomeForm
    template_name = 'income/income_form.html'
    success_url = reverse_lazy('income:list')

    def get_form_kwargs(self):
        """Pasa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Agrega categorías para los botones visuales."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context
    
    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'Ingreso registrado: {self.object.decription} - {self.object.formatted_amount}'
        )
        return response
    
    def form_invalid(self, form):
        """Muestra errores."""
        messages.error(self.request, 'Corregí los errores del formulario.')
        return super().form_invalid(form)


class IncomeUpdateView(LoginRequiredMixin, UpdateView):
    """Editar ingreso existente."""

    model = Income
    form_class = IncomeForm
    template_name = 'income/income_form.html'
    success_url = reverse_lazy('income:list')

    def get_queryset(self):
        """Solo permite editar ingresos propios."""
        return Income.objects.filter(user=self.request.user)
    
    def get_form_kwargs(self):
        """Pasa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Agrega categorías para los botones visuales."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.get_income_categories(self.request.user)
        context['is_edit'] = True
        return context
    
    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(self.request, 'Ingreso actualizado correctamente.')
        return response


class IncomeDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar ingreso (soft delete)."""
    
    model = Income
    template_name = 'income/income_confirm_delete.html'
    success_url = reverse_lazy('income:list')

    def get_queryset(self):
        """Solo permite eliminar ingresos propios."""
        return Income.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Realiza soft delete."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, 'Ingreso eliminado correctamente.')
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)


class IncomeDetailView(LoginRequiredMixin, DetailView):
    """Ver detalle de un ingreso."""
    
    model = Income
    template_name = 'income/income_detail.html'
    context_object_name = 'income'

    def get_queryset(self):
        """Solo permite ver ingresos propios."""
        return Income.objects.filter(user=self.request.user).select_related('category')
