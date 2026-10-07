"""Vistas para gastos recurrentes."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.utils import get_month_name
from apps.core.views import UserFormKwargsMixin

from .forms import RecurringExpenseForm
from .models import RecurringExpense


class RecurringExpenseListView(LoginRequiredMixin, ListView):
    model = RecurringExpense
    template_name = "recurring/recurring_list.html"
    context_object_name = "recurrents"

    def get_queryset(self):
        return (
            RecurringExpense.objects.filter(user=self.request.user)
            .select_related("category", "category__parent")
            .order_by("due_day", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month, year = today.month, today.year
        show_inactive = self.request.GET.get("inactive") == "1"

        all_items = []
        for rec in context["recurrents"]:
            last = rec.last_expense
            all_items.append(
                {
                    "rec": rec,
                    "status": rec.status_for(month, year),
                    "last_expense": last,
                    "display_amount": rec.display_amount,
                    "is_estimated_amount": rec.is_estimated_amount,
                }
            )

        active_items = [i for i in all_items if i["rec"].is_active]
        inactive_items = [i for i in all_items if not i["rec"].is_active]

        context["items"] = all_items if show_inactive else active_items
        context["inactive_count"] = len(inactive_items)
        context["show_inactive"] = show_inactive
        context["current_month"] = f"{get_month_name(today.month)} {today.year}"
        context["total_active"] = len(active_items)
        context["total_paid"] = sum(1 for i in active_items if i["status"] == "paid")
        return context


class RecurringExpenseCreateView(LoginRequiredMixin, UserFormKwargsMixin, CreateView):
    model = RecurringExpense
    form_class = RecurringExpenseForm
    template_name = "recurring/recurring_form.html"
    success_url = reverse_lazy("recurring:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, f"Gasto recurrente '{self.object.name}' creado correctamente."
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request, "No pudimos guardar el gasto recurrente. Revisá los campos marcados."
        )
        return super().form_invalid(form)


class RecurringExpenseUpdateView(LoginRequiredMixin, UserFormKwargsMixin, UpdateView):
    model = RecurringExpense
    form_class = RecurringExpenseForm
    template_name = "recurring/recurring_form.html"
    success_url = reverse_lazy("recurring:list")

    def get_queryset(self):
        return RecurringExpense.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Gasto recurrente '{self.object.name}' actualizado correctamente."
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request, "No pudimos guardar el gasto recurrente. Revisá los campos marcados."
        )
        return super().form_invalid(form)


class RecurringExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = RecurringExpense
    template_name = "recurring/recurring_confirm_delete.html"
    success_url = reverse_lazy("recurring:list")

    def get_queryset(self):
        return RecurringExpense.objects.filter(user=self.request.user)

    def form_valid(self, form):
        name = self.get_object().name
        response = super().form_valid(form)
        messages.success(self.request, f"Gasto recurrente '{name}' eliminado correctamente.")
        return response
