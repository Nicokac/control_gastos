from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.v1.pagination import ConfigurablePageNumberPagination
from apps.api.v1.serializers.recurring import RecurringExpenseSerializer
from apps.recurring.models import RecurringExpense


class RecurringExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = RecurringExpenseSerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        return (
            RecurringExpense.objects.filter(user=self.request.user)
            .select_related("category", "category__parent")
            .order_by("due_day", "name")
        )

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        from apps.expenses.models import Expense

        rec = self.get_object()
        today = timezone.localdate()

        if rec.is_paid_in(today.month, today.year):
            return Response(
                {"detail": "Este gasto ya fue registrado este mes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = request.data.get("amount")
        if not amount:
            last = rec.last_expense
            amount = last.amount if last else None
        if not amount:
            return Response(
                {"detail": "Indicá el monto del pago."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expense = Expense.objects.create(
            user=request.user,
            date=today,
            category=rec.category,
            description=rec.name,
            amount=amount,
            currency="ARS",
            recurring=rec,
        )
        rec.auto_deactivate_if_complete()
        return Response(
            {"detail": "Pago registrado.", "expense_id": expense.pk}, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="unmark-paid")
    def unmark_paid(self, request, pk=None):
        rec = self.get_object()
        today = timezone.localdate()

        expense = (
            rec.expenses.filter(date__month=today.month, date__year=today.year)
            .order_by("-date")
            .first()
        )

        if not expense:
            return Response(
                {"detail": "No hay pago registrado este mes para este gasto."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expense.delete()

        if not rec.is_active and rec.is_installment:
            rec.is_active = True
            rec.save(update_fields=["is_active"])

        return Response({"detail": "Pago revertido."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        today = timezone.localdate()
        items = [
            rec
            for rec in self.get_queryset().filter(is_active=True)
            if rec.status_for(today.month, today.year) in ("pending", "overdue")
        ]
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
