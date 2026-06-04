from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.expenses.models import Expense
from apps.income.models import Income
from apps.recurring.models import RecurringExpense
from apps.savings.models import Saving, SavingStatus


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        try:
            month = int(request.query_params.get("month", today.month))
            year = int(request.query_params.get("year", today.year))
        except (ValueError, TypeError):
            month, year = today.month, today.year

        month = max(1, min(month, 12))
        year = max(2020, year)

        total_expenses = Expense.objects.filter(
            user=user, date__month=month, date__year=year
        ).aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")

        total_income = Income.objects.filter(
            user=user, date__month=month, date__year=year
        ).aggregate(total=Sum("amount_ars"))["total"] or Decimal("0")

        balance = total_income - total_expenses

        expenses_by_category = list(
            Expense.objects.filter(user=user, date__month=month, date__year=year)
            .values("category__id", "category__name", "category__color", "category__icon")
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")
        )

        income_by_category = list(
            Income.objects.filter(user=user, date__month=month, date__year=year)
            .values("category__id", "category__name", "category__color", "category__icon")
            .annotate(total=Sum("amount_ars"))
            .order_by("-total")
        )

        savings = Saving.objects.filter(user=user, status=SavingStatus.ACTIVE).values(
            "id", "name", "target_amount", "current_amount", "currency"
        )
        savings_progress = [
            {
                **s,
                "progress_percentage": round(
                    float(s["current_amount"]) / float(s["target_amount"]) * 100, 1
                )
                if s["target_amount"] > 0
                else 0,
            }
            for s in savings
        ]

        pending_recurring = [
            {
                "id": rec.pk,
                "name": rec.name,
                "due_day": rec.due_day,
                "status": rec.status_for(month, year),
                "last_amount": str(rec.last_expense.amount_ars) if rec.last_expense else None,
            }
            for rec in RecurringExpense.objects.filter(user=user, is_active=True).select_related(
                "category"
            )
            if rec.status_for(month, year) in ("pending", "overdue")
        ]

        recent_expenses = list(
            Expense.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")
            .values(
                "id",
                "date",
                "description",
                "amount_ars",
                "category__name",
                "category__color",
                "category__icon",
            )[:5]
        )
        recent_income = list(
            Income.objects.filter(user=user)
            .select_related("category")
            .order_by("-date", "-created_at")
            .values(
                "id",
                "date",
                "description",
                "amount_ars",
                "category__name",
                "category__color",
                "category__icon",
            )[:5]
        )

        return Response(
            {
                "month": month,
                "year": year,
                "total_expenses": str(total_expenses),
                "total_income": str(total_income),
                "balance": str(balance),
                "expenses_by_category": [
                    {
                        "category_id": e["category__id"],
                        "category_name": e["category__name"],
                        "category_color": e["category__color"],
                        "category_icon": e["category__icon"],
                        "total": str(e["total"]),
                    }
                    for e in expenses_by_category
                ],
                "income_by_category": [
                    {
                        "category_id": e["category__id"],
                        "category_name": e["category__name"],
                        "category_color": e["category__color"],
                        "category_icon": e["category__icon"],
                        "total": str(e["total"]),
                    }
                    for e in income_by_category
                ],
                "savings_progress": savings_progress,
                "pending_recurring": pending_recurring,
                "recent_transactions": {
                    "expenses": recent_expenses,
                    "income": recent_income,
                },
            }
        )
