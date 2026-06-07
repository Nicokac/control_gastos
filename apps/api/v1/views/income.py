from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.v1.pagination import ConfigurablePageNumberPagination
from apps.api.v1.serializers.income import IncomeSerializer
from apps.income.models import Income


class IncomeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = IncomeSerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Income.objects.none()

        qs = (
            Income.objects.filter(user=self.request.user)
            .select_related("category", "category__parent")
            .order_by("-date", "-created_at")
        )
        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        category = self.request.query_params.get("category")

        if month:
            qs = qs.filter(date__month=month)
        if year:
            qs = qs.filter(date__year=year)
        if category:
            qs = qs.filter(category__pk=category)
        return qs
