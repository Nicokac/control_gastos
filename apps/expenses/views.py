import logging

from django.contrib import messages
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
        qs = super().get_queryset().select_related("category", "category__parent", "saving")

        has_filters = any(
            key in self.request.GET
            for key in [
                "month",
                "year",
                "category",
                "subcategory",
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
            today = timezone.localdate()
            month = str(today.month)
            year = str(today.year)

        category = self.request.GET.get("category")
        subcategory = self.request.GET.get("subcategory")
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

        if subcategory:
            # subcategoría específica tiene prioridad sobre el grupo
            qs = qs.filter(category_id=subcategory)
        elif category:
            # category contiene el pk de un grupo (parent); filtramos sus subcategorías
            qs = qs.filter(category__parent_id=category)
        if payment_method:
            qs = qs.filter(payment_method=payment_method)
        if expense_type:
            qs = qs.filter(expense_type=expense_type)

        qs = qs.order_by("-date", "-created_at")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        has_filters = any(
            key in self.request.GET
            for key in [
                "month",
                "year",
                "category",
                "subcategory",
                "date_from",
                "date_to",
                "payment_method",
                "expense_type",
            ]
        )

        if has_filters:
            form_data = self.request.GET
        else:
            today = timezone.localdate()
            form_data = {"month": today.month, "year": today.year}

        context["filter_form"] = ExpenseFilterForm(form_data, user=self.request.user)

        qs = self.object_list

        total = qs.aggregate(total=Sum("amount_ars"))["total"] or 0
        context["total"] = total

        expense_type_labels = dict(ExpenseType.choices)
        type_classified = qs.exclude(expense_type="").aggregate(s=Sum("amount_ars"))["s"] or 0
        type_unclassified = (total - type_classified) if total else 0
        expense_type_summary = [
            {
                "label": expense_type_labels.get(row["expense_type"], row["expense_type"]),
                "subtotal": row["subtotal"],
            }
            for row in qs.exclude(expense_type="")
            .values("expense_type")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("expense_type")
        ]
        if type_unclassified > 0:
            expense_type_summary.append({"label": "Sin clasificar", "subtotal": type_unclassified})
        context["expense_type_summary"] = expense_type_summary

        payment_method_labels = dict(PaymentMethod.choices)
        method_classified = qs.exclude(payment_method="").aggregate(s=Sum("amount_ars"))["s"] or 0
        method_unclassified = (total - method_classified) if total else 0
        payment_method_summary = [
            {
                "label": payment_method_labels.get(row["payment_method"], row["payment_method"]),
                "subtotal": row["subtotal"],
            }
            for row in qs.exclude(payment_method="")
            .values("payment_method")
            .annotate(subtotal=Sum("amount_ars"))
            .order_by("payment_method")
        ]
        if method_unclassified > 0:
            payment_method_summary.append(
                {"label": "Sin clasificar", "subtotal": method_unclassified}
            )
        context["payment_method_summary"] = payment_method_summary

        return context


class ExpenseCreateView(UserOwnedCreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_message(self):
        obj = self.object
        return f"Gasto registrado: {obj.description} - {obj.formatted_amount}"

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar el gasto. Revisá los campos marcados. Monto, categoría y fecha son obligatorios.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories_by_group"] = Category.get_categories_by_group(
            self.request.user, "EXPENSE"
        )
        return context


class ExpenseUpdateView(UserOwnedUpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expenses:list")

    def get_success_message(self):
        obj = self.object
        return f"Gasto actualizado: {obj.description} - {obj.formatted_amount}"

    def form_invalid(self, form):
        messages.error(
            self.request,
            "No pudimos guardar el gasto. Revisá los campos marcados.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories_by_group"] = Category.get_categories_by_group(
            self.request.user, "EXPENSE"
        )
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
