from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.v1.serializers.shared_expenses import (
    HouseholdMemberSerializer,
    SharedExpenseSerializer,
)
from apps.shared_expenses.models import HouseholdMember, SharedExpense


class HouseholdMemberViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = HouseholdMemberSerializer

    def get_queryset(self):
        return HouseholdMember.objects.filter(user=self.request.user)


class SharedExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SharedExpenseSerializer

    def get_queryset(self):
        qs = (
            SharedExpense.objects.filter(user=self.request.user)
            .select_related("category", "paid_by")
            .order_by("-date", "-created_at")
        )
        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        if month:
            qs = qs.filter(date__month=month)
        if year:
            qs = qs.filter(date__year=year)
        return qs
