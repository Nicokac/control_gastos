import logging

from django.db.models import Sum

from apps.categories.models import Category
from apps.core.views import (
    UserOwnedCreateView,
    UserOwnedDeleteView,
    UserOwnedDetailView,
    UserOwnedListView,
    UserOwnedUpdateView,
)

from .forms import ExpenseFilterForm, ExpenseForm
from .models import Expense

logger = logging.getLogger(__name__)


class ExpenseListView(UserOwnedListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        qs = super().get_queryset().select_related("category", "saving")
        # Aplicar filtros de mes/año/categoría
        month = self.request.GET.get("month")
        year = self.request.GET.get("year")
        category = self.request.GET.get("category")

        if month:
            try:
                month = int(month)
                if 1 <= month <= 12:
                    qs = qs.filter(date__month=month)
            except ValueError:
                pass

        if year:
            try:
                year = int(year)
                if 1900 <= year <= 2100:
                    qs = qs.filter(date__year=year)
            except ValueError:
                pass

        if category:
            qs = qs.filter(category_id=category)

        return qs.order_by("-date", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = ExpenseFilterForm(self.request.GET, user=self.request.user)
        # Calcular total del queryset filtrado
        total = self.get_queryset().aggregate(total=Sum("amount_ars"))["total"] or 0
        context["total_amount"] = total
        return context


class ExpenseCreateView(UserOwnedCreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = "/expenses/"

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
    success_url = "/expenses/"

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
    success_url = "/expenses/"

    def get_success_message(self, obj):
        return f"Gasto '{obj.description}' eliminado correctamente."


class ExpenseDetailView(UserOwnedDetailView):
    model = Expense
    template_name = "expenses/expense_detail.html"
    context_object_name = "expense"

    def get_queryset(self):
        return super().get_queryset().select_related("category", "saving")
