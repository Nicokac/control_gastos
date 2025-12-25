"""
Vistas para gestión de presupuestos.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.utils import timezone
from django.http import HttpResponseRedirect
from decimal import Decimal

from .models import Budget
from .forms import BudgetForm, BudgetFilterForm, CopyBudgetsForm
from apps.categories.models import Category


class BudgetListView(LoginRequiredMixin, ListView):
    """Lista de presupuestos del usuario con filtros."""
    
    model = Budget
    template_name = 'budgets/budget_list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        """Filtra presupuestos del usuario actual."""
        queryset = Budget.objects.filter(
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
                    queryset = queryset.filter(month=month)
            
            if year:
                year = int(year)
                if 2020 <= year <= 2100:
                    queryset = queryset.filter(year=year)
            
            if category:
                category = int(category)
                queryset = queryset.filter(category_id=category)
        except (ValueError, TypeError):
            pass  # Ignorar parámetros inválidos
        
        # Si no hay filtros, mostrar mes actual por defecto
        if not month and not year and not category:
            today = timezone.now().date()
            queryset = queryset.filter(month=today.month, year=today.year)
        
        return queryset

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Formulario de filtros
        context['filter_form'] = BudgetFilterForm(
            data=self.request.GET or None,
            user=self.request.user
        )
        
        # Determinar período actual
        month = self.request.GET.get('month')
        year = self.request.GET.get('year')
        
        if not month or not year:
            today = timezone.now().date()
            month = today.month
            year = today.year
        else:
            try:
                month = int(month)
                year = int(year)
            except (ValueError, TypeError):
                today = timezone.now().date()
                month = today.month
                year = today.year
        
        context['current_month'] = month
        context['current_year'] = year
        
        # Resumen del período
        context['summary'] = Budget.get_monthly_summary(
            self.request.user,
            month,
            year
        )
        
        # Nombre del mes
        from apps.core.utils import MONTHS
        context['period_name'] = f"{MONTHS.get(month, '')} {year}"
        
        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo presupuesto."""
    
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'
    success_url = reverse_lazy('budgets:list')

    def get_form_kwargs(self):
        """Pasa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'Presupuesto para {self.object.category.name} creado correctamente.'
        )
        return response

    def form_invalid(self, form):
        """Muestra errores."""
        messages.error(self.request, 'Corregí los errores del formulario.')
        return super().form_invalid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    """Editar presupuesto existente."""
    
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'
    success_url = reverse_lazy('budgets:list')

    def get_queryset(self):
        """Solo permite editar presupuestos propios."""
        return Budget.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        """Pasa el usuario al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """Agrega datos al contexto."""
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        """Guarda y muestra mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(self.request, 'Presupuesto actualizado correctamente.')
        return response


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar presupuesto (soft delete)."""
    
    model = Budget
    template_name = 'budgets/budget_confirm_delete.html'
    success_url = reverse_lazy('budgets:list')

    def get_queryset(self):
        """Solo permite eliminar presupuestos propios."""
        return Budget.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Realiza soft delete."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, 'Presupuesto eliminado correctamente.')
        return HttpResponseRedirect(self.success_url)


class BudgetDetailView(LoginRequiredMixin, DetailView):
    """Ver detalle de un presupuesto."""
    
    model = Budget
    template_name = 'budgets/budget_detail.html'
    context_object_name = 'budget'

    def get_queryset(self):
        """Solo permite ver presupuestos propios."""
        return Budget.objects.filter(user=self.request.user).select_related('category')

    def get_context_data(self, **kwargs):
        """Agrega gastos del período al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Obtener gastos de esta categoría en el período
        from apps.expenses.models import Expense
        
        context['expenses'] = Expense.objects.filter(
            user=self.request.user,
            category=self.object.category,
            date__month=self.object.month,
            date__year=self.object.year,
            is_active=True
        ).order_by('-date')[:10]
        
        return context


class CopyBudgetsView(LoginRequiredMixin, FormView):
    """Copiar presupuestos del mes anterior."""
    
    form_class = CopyBudgetsForm
    template_name = 'budgets/budget_copy.html'
    success_url = reverse_lazy('budgets:list')

    def form_valid(self, form):
        """Copia los presupuestos."""
        target_month = int(form.cleaned_data['target_month'])
        target_year = int(form.cleaned_data['target_year'])
        
        created = Budget.copy_from_previous_month(
            self.request.user,
            target_month,
            target_year
        )
        
        if created:
            messages.success(
                self.request,
                f'Se copiaron {len(created)} presupuesto(s) al período seleccionado.'
            )
        else:
            messages.warning(
                self.request,
                'No se encontraron presupuestos para copiar o ya existen en el período destino.'
            )
        
        return super().form_valid(form)