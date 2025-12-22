"""
Vistas para gestión de ahorro.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseRedirect
from decimal import Decimal

from .models import Saving, SavingMovement, SavingStatus
from .forms import SavingForm, SavingMovementForm, SavingFilterForm


class SavingListView(LoginRequiredMixin, ListView):
    """Lista de metas de ahorro del usuario."""
    
    model = Saving
    template_name = 'savings/saving_list.html'
    context_object_name = 'savings'

    def get_queryset(self):
        """Filtra metas del usuario actual con validación de parámetros."""
        queryset = Saving.objects.filter(user=self.request.user)
        
        # Aplicar filtro de estado con validación
        status = self.request.GET.get('status')
        
        if status:
            # Validar que sea un status válido
            valid_statuses = [s[0] for s in SavingStatus.choices]
            if status in valid_statuses:
                queryset = queryset.filter(status=status)
            # Si no es válido, ignorar el filtro
        
        return queryset

    def get_context_data(self, **kwargs):
        """Agrega datos adicionales al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Formulario de filtros
        context['filter_form'] = SavingFilterForm(data=self.request.GET or None)
        
        # Obtener metas activas del usuario
        user_savings = Saving.objects.filter(user=self.request.user, is_active=True)
        active_savings = user_savings.filter(status=SavingStatus.ACTIVE)
        
        # Contadores
        context['active_count'] = active_savings.count()
        context['completed_count'] = user_savings.filter(status=SavingStatus.COMPLETED).count()
        
        # Resumen global de metas activas
        from django.db.models import Sum
        
        totals = active_savings.aggregate(
            total_target=Sum('target_amount'),
            total_current=Sum('current_amount')
        )
        
        total_target = totals['total_target'] or Decimal('0')
        total_current = totals['total_current'] or Decimal('0')
        total_remaining = total_target - total_current
        
        # Calcular progreso global
        if total_target > 0:
            overall_progress = round((total_current / total_target) * 100, 1)
        else:
            overall_progress = 0
        
        context['summary'] = {
            'total_target': total_target,
            'total_current': total_current,
            'total_remaining': max(total_remaining, Decimal('0')),
            'overall_progress': min(overall_progress, 100),
        }
        
        # Total ahorrado (para compatibilidad)
        context['total_saved'] = total_current
        
        return context


class SavingCreateView(LoginRequiredMixin, CreateView):
    """Crear nueva meta de ahorro."""
    
    model = Saving
    form_class = SavingForm
    template_name = 'savings/saving_form.html'
    success_url = reverse_lazy('savings:list')

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
            f'Meta de ahorro "{self.object.name}" creada correctamente.'
        )
        return response


class SavingUpdateView(LoginRequiredMixin, UpdateView):
    """Editar meta de ahorro existente."""
    
    model = Saving
    form_class = SavingForm
    template_name = 'savings/saving_form.html'
    success_url = reverse_lazy('savings:list')

    def get_queryset(self):
        """Solo permite editar metas propias."""
        return Saving.objects.filter(user=self.request.user)

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
        messages.success(self.request, 'Meta de ahorro actualizada correctamente.')
        return response


class SavingDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar meta de ahorro (soft delete)."""
    
    model = Saving
    template_name = 'savings/saving_confirm_delete.html'
    success_url = reverse_lazy('savings:list')

    def get_queryset(self):
        """Solo permite eliminar metas propias."""
        return Saving.objects.filter(user=self.request.user)

    def form_valid(self, form):
        """Realiza soft delete."""
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(self.request, 'Meta de ahorro eliminada correctamente.')
        return HttpResponseRedirect(self.success_url)


class SavingDetailView(LoginRequiredMixin, DetailView):
    """Ver detalle de una meta de ahorro."""
    
    model = Saving
    template_name = 'savings/saving_detail.html'
    context_object_name = 'saving'

    def get_queryset(self):
        """Solo permite ver metas propias."""
        return Saving.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """Agrega movimientos paginados al contexto."""
        context = super().get_context_data(**kwargs)
        
        # Paginar movimientos
        from django.core.paginator import Paginator
        
        movements_list = self.object.movements.all().order_by('-date', '-created_at')
        paginator = Paginator(movements_list, 10)  # 10 movimientos por página
        
        page = self.request.GET.get('page', 1)
        
        try:
            movements = paginator.get_page(page)
        except:
            movements = paginator.get_page(1)
        
        context['movements'] = movements
        context['movement_form'] = SavingMovementForm(saving=self.object)
        
        return context


class SavingMovementCreateView(LoginRequiredMixin, FormView):
    """Agregar movimiento a una meta de ahorro."""
    
    form_class = SavingMovementForm
    template_name = 'savings/saving_movement_form.html'

    def dispatch(self, request, *args, **kwargs):
        """Obtiene la meta de ahorro."""
        self.saving = get_object_or_404(
            Saving, 
            pk=kwargs['pk'], 
            user=request.user
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Pasa la meta al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs['saving'] = self.saving
        return kwargs

    def get_context_data(self, **kwargs):
        """Agrega la meta al contexto."""
        context = super().get_context_data(**kwargs)
        context['saving'] = self.saving
        return context

    def form_valid(self, form):
        """Guarda el movimiento."""
        movement = form.save()
        
        if movement.is_deposit:
            messages.success(
                self.request, 
                f'Depósito de ${movement.amount:,.2f} registrado correctamente.'
            )
        else:
            messages.success(
                self.request, 
                f'Retiro de ${movement.amount:,.2f} registrado correctamente.'
            )
        
        return redirect('savings:detail', pk=self.saving.pk)

    def form_invalid(self, form):
        """Muestra errores."""
        messages.error(self.request, 'Corregí los errores del formulario.')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('savings:detail', kwargs={'pk': self.saving.pk})