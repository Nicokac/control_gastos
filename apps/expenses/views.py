import logging

from django.urls import reverse_lazy
from django.utils import timezone

from apps.categories.models import Category
from apps.core.views import (
    UserOwnedCreateView,
    UserOwnedDeleteView,
    UserOwnedDetailView,
    UserOwnedListView,
    UserOwnedUpdateView,
)

from .forms import ExpenseForm
from .models import Expense

logger = logging.getLogger(__name__)


class ExpenseListView(UserOwnedListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        if hasattr(self, "_cached_queryset"):
            return self._cached_queryset

        qs = super().get_queryset().select_related("category", "saving")

        # Aplicar filtros de mes/año/categoría
        # Si no hay parámetros GET, usar mes/año actual como default
        has_filters = any(
            key in self.request.GET
            for key in [
                "month",
                "year",
                "category",
                "date_from",
                "date_to",
                "payment_method",
                "expense_type",
            ]
        )

        if has_filters:
            month = self.request.GET.get("month")
            year = self.request.GET.get("year")
        else:
            # Default: mes y año actual
            today = timezone.now().date()
            month = str(today.month)
            year = str(today.year)

        category = self.request.GET.get("category")
        payment_method = self.request.GET.get("payment_method")
        expense_type = self.request.GET.get("expense_type")

        if month:
            try:
                month_int = int(month)
                if 1 <= month_int <= 12:
                    qs = qs.filter(date__month=month_int)
            except ValueError:
                pass

        if year:
            try:
                year_int = int(year)
                if 1900 <= year_int <= 2100:
                    qs = qs.filter(date__year=year_int)
            except ValueError:
                pass

        if category:
            qs = qs.filter(category_id=category)

        if payment_method:
            qs = qs.filter(payment_method=payment_method)

        if expense_type:
            qs = qs.filter(expense_type=expense_type)

        qs = qs.order_by("-date", "-created_at")

        self._cached_queryset = qs
        return qs


class ExpenseCreateView(UserOwnedCreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_message(self):
        obj = self.object
        return f"Gasto registrado: {obj.description} - {obj.formatted_amount}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.get_expense_categories(self.request.user)
        return context


class ExpenseUpdateView(UserOwnedUpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_message(self):
        obj = self.object
        return f"Gasto actualizado: {obj.description} - {obj.formatted_amount}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.get_expense_categories(self.request.user)
        return context


class ExpenseDeleteView(UserOwnedDeleteView):
    model = Expense
    template_name = "expenses/expense_confirm_delete.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_message(self, obj):
        return f"Gasto '{obj.description}' eliminado correctamente."


class ExpenseDetailView(UserOwnedDetailView):
    model = Expense
    template_name = "expenses/expense_detail.html"
    context_object_name = "expense"

    def get_queryset(self):
        return super().get_queryset().select_related("category", "saving")
