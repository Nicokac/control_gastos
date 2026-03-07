import logging

from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils import timezone

from apps.categories.models import Category
from apps.core.constants import ExpenseType, PaymentMethod
from apps.core.utils import get_month_date_range_exclusive
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
        if hasattr(self, "_cached_queryset"):
            return self._cached_queryset

        qs = super().get_queryset().select_related("category", "saving")

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
            today = timezone.now().date()
            month = str(today.month)
            year = str(today.year)

        category = self.request.GET.get("category")
        payment_method = self.request.GET.get("payment_method")
        expense_type = self.request.GET.get("expense_type")

        # ✅ Mes/año -> rango [start, end)
        if month and year:
            try:
                month_int = int(month)
                year_int = int(year)
                if 1 <= month_int <= 12 and 1900 <= year_int <= 2100:
                    start, end = get_month_date_range_exclusive(month_int, year_int)
                    qs = qs.filter(date__gte=start, date__lt=end)
            except ValueError:
                pass
        else:
            # Si viene solo year, mantenemos comportamiento actual
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
            form_data = self.request.GET
        else:
            today = timezone.now().date()
            form_data = {"month": today.month, "year": today.year}

        context["filter_form"] = ExpenseFilterForm(form_data, user=self.request.user)

        qs = getattr(self, "_cached_queryset", self.object_list)

        total = qs.aggregate(total=Sum("amount_ars"))["total"] or 0
        context["total"] = total

        expense_type_labels = dict(ExpenseType.choices)
        context["expense_type_summary"] = [
            {
                "label": expense_type_labels.get(row["expense_type"], row["expense_type"]),
                "subtotal": row["subtotal"],
            }
            for row in qs.exclude(expense_type="")
            .values("expense_type")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("expense_type")
        ]

        payment_method_labels = dict(PaymentMethod.choices)
        context["payment_method_summary"] = [
            {
                "label": payment_method_labels.get(row["payment_method"], row["payment_method"]),
                "subtotal": row["subtotal"],
            }
            for row in qs.exclude(payment_method="")
            .values("payment_method")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("payment_method")
        ]

        return context


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
