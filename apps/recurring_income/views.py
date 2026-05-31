"""Vistas para ingresos recurrentes."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.core.utils import get_month_name
from apps.core.views import UserFormKwargsMixin

from .forms import RecurringIncomeForm
from .models import RecurringIncome


class RecurringIncomeListView(LoginRequiredMixin, ListView):
    model = RecurringIncome
    template_name = "recurring_income/recurring_income_list.html"
    context_object_name = "recurrents"

    def get_queryset(self):
        return (
            RecurringIncome.objects.filter(user=self.request.user)
            .select_related("category", "category__parent")
            .order_by("expected_day", "name")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month, year = today.month, today.year
        show_inactive = self.request.GET.get("inactive") == "1"

        all_items = []
        for rec in context["recurrents"]:
            last = rec.last_income
            all_items.append(
                {
                    "rec": rec,
                    "status": rec.status_for(month, year),
                    "last_income": last,
                }
            )

        active_items = [i for i in all_items if i["rec"].is_active]
        inactive_items = [i for i in all_items if not i["rec"].is_active]

        context["items"] = all_items if show_inactive else active_items
        context["inactive_count"] = len(inactive_items)
        context["show_inactive"] = show_inactive
        context["current_month"] = f"{get_month_name(today.month)} {today.year}"
        context["total_active"] = len(active_items)
        context["total_collected"] = sum(1 for i in active_items if i["status"] == "collected")
        return context


class RecurringIncomeCreateView(LoginRequiredMixin, UserFormKwargsMixin, CreateView):
    model = RecurringIncome
    form_class = RecurringIncomeForm
    template_name = "recurring_income/recurring_income_form.html"
    success_url = reverse_lazy("recurring_income:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = False
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, f"Ingreso recurrente '{self.object.name}' creado correctamente."
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request, "No pudimos guardar el ingreso recurrente. Revisá los campos marcados."
        )
        return super().form_invalid(form)


class RecurringIncomeUpdateView(LoginRequiredMixin, UserFormKwargsMixin, UpdateView):
    model = RecurringIncome
    form_class = RecurringIncomeForm
    template_name = "recurring_income/recurring_income_form.html"
    success_url = reverse_lazy("recurring_income:list")

    def get_queryset(self):
        return RecurringIncome.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Ingreso recurrente '{self.object.name}' actualizado correctamente."
        )
        return response

    def form_invalid(self, form):
        messages.error(
            self.request, "No pudimos guardar el ingreso recurrente. Revisá los campos marcados."
        )
        return super().form_invalid(form)


class RecurringIncomeDeleteView(LoginRequiredMixin, DeleteView):
    model = RecurringIncome
    template_name = "recurring_income/recurring_income_confirm_delete.html"
    success_url = reverse_lazy("recurring_income:list")

    def get_queryset(self):
        return RecurringIncome.objects.filter(user=self.request.user)

    def form_valid(self, form):
        name = self.get_object().name
        response = super().form_valid(form)
        messages.success(self.request, f"Ingreso recurrente '{name}' eliminado correctamente.")
        return response
