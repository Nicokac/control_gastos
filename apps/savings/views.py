"""
Vistas para gestión de ahorro.
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView

from apps.core.views import (
    UserOwnedCreateView,
    UserOwnedDeleteView,
    UserOwnedDetailView,
    UserOwnedListView,
    UserOwnedUpdateView,
)

from .forms import SavingFilterForm, SavingForm, SavingMovementForm
from .models import Saving, SavingStatus


class SavingListView(UserOwnedListView):
    """Lista de metas de ahorro del usuario."""

    model = Saving
    template_name = "savings/saving_list.html"
    context_object_name = "savings"

    def get_queryset(self):
        """Filtra metas del usuario actual con validación de parámetros."""
        queryset = super().get_queryset()

        # Aplicar filtro de estado con validación
        status = self.request.GET.get("status")

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
        context["filter_form"] = SavingFilterForm(data=self.request.GET or None)

        # Obtener metas activas del usuario
        user_savings = Saving.objects.filter(user=self.request.user, is_active=True)
        active_savings = user_savings.filter(status=SavingStatus.ACTIVE)

        # Contadores
        context["active_count"] = active_savings.count()
        context["completed_count"] = user_savings.filter(status=SavingStatus.COMPLETED).count()

        # Resumen global de metas activas
        from django.db.models import Sum

        totals = active_savings.aggregate(
            total_target=Sum("target_amount"), total_current=Sum("current_amount")
        )

        total_target = totals["total_target"] or Decimal("0")
        total_current = totals["total_current"] or Decimal("0")
        total_remaining = total_target - total_current

        # Calcular progreso global
        if total_target > 0:
            overall_progress = round((total_current / total_target) * 100, 1)
        else:
            overall_progress = 0

        context["summary"] = {
            "total_target": total_target,
            "total_current": total_current,
            "total_remaining": max(total_remaining, Decimal("0")),
            "overall_progress": min(overall_progress, 100),
        }

        # Total ahorrado (para compatibilidad)
        context["total_saved"] = total_current

        return context


class SavingCreateView(UserOwnedCreateView):
    """Crear nueva meta de ahorro."""

    model = Saving
    form_class = SavingForm
    template_name = "savings/saving_form.html"
    success_url = reverse_lazy("savings:list")

    def get_success_message(self):
        return f'Meta de ahorro "{self.object.name}" creada correctamente.'


class SavingUpdateView(UserOwnedUpdateView):
    """Editar meta de ahorro existente."""

    model = Saving
    form_class = SavingForm
    template_name = "savings/saving_form.html"
    success_url = reverse_lazy("savings:list")

    def get_success_message(self):
        return f'Meta de ahorro "{self.object.name}" actualizada correctamente.'


class SavingDeleteView(UserOwnedDeleteView):
    """Eliminar meta de ahorro."""

    model = Saving
    template_name = "savings/saving_confirm_delete.html"
    success_url = reverse_lazy("savings:list")

    def get_success_message(self, obj):
        return f'Meta de ahorro "{obj.name}" eliminada correctamente.'


class SavingDetailView(UserOwnedDetailView):
    """Ver detalle de una meta de ahorro."""

    model = Saving
    template_name = "savings/saving_detail.html"
    context_object_name = "saving"

    def get_context_data(self, **kwargs):
        """Agrega movimientos paginados al contexto."""
        context = super().get_context_data(**kwargs)

        # Paginar movimientos
        movements_list = self.object.movements.all().order_by("-date", "-created_at")
        paginator = Paginator(movements_list, 10)  # 10 movimientos por página

        page_number = self.request.GET.get("page", 1)

        try:
            movements = paginator.page(page_number)
        except PageNotAnInteger:
            movements = paginator.page(1)
        except EmptyPage:
            movements = paginator.page(paginator.num_pages)

        context["movements"] = movements

        return context


class SavingMovementCreateView(LoginRequiredMixin, FormView):
    """Agregar movimiento a una meta de ahorro."""

    form_class = SavingMovementForm
    template_name = "savings/saving_movement_form.html"

    def get_saving(self):
        """Obtiene la meta de ahorro de forma lazy."""
        if not hasattr(self, "_saving"):
            self._saving = get_object_or_404(Saving, pk=self.kwargs["pk"], user=self.request.user)
        return self._saving

    def get_form_kwargs(self):
        """Pasa la meta al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs["saving"] = self.get_saving()
        return kwargs

    def get_context_data(self, **kwargs):
        """Agrega la meta al contexto."""
        context = super().get_context_data(**kwargs)
        context["saving"] = self.get_saving()
        return context

    def form_valid(self, form):
        """Guarda el movimiento."""
        movement = form.save()

        if movement.is_deposit:
            messages.success(
                self.request, f"Depósito de ${movement.amount:,.2f} registrado correctamente."
            )
        else:
            messages.success(
                self.request, f"Retiro de ${movement.amount:,.2f} registrado correctamente."
            )

        return redirect("savings:detail", pk=self.get_saving().pk)

    def form_invalid(self, form):
        """Muestra errores."""
        messages.error(self.request, "Corregí los errores del formulario.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse("savings:detail", kwargs={"pk": self.get_saving().pk})
