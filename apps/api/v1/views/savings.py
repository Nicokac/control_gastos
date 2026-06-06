from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.v1.pagination import ConfigurablePageNumberPagination
from apps.api.v1.serializers.savings import (
    DepositWithdrawSerializer,
    SavingMovementSerializer,
    SavingSerializer,
)
from apps.savings.models import Saving, SavingMovement


class SavingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SavingSerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        return Saving.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=True, methods=["post"])
    def deposit(self, request, pk=None):
        saving = self.get_object()
        serializer = DepositWithdrawSerializer(data=request.data)
        if serializer.is_valid():
            saving.add_deposit(
                amount=serializer.validated_data["amount"],
                description=serializer.validated_data.get("description", ""),
            )
            return Response(SavingSerializer(saving, context={"request": request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        saving = self.get_object()
        serializer = DepositWithdrawSerializer(data=request.data)
        if serializer.is_valid():
            try:
                saving.add_withdrawal(
                    amount=serializer.validated_data["amount"],
                    description=serializer.validated_data.get("description", ""),
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(SavingSerializer(saving, context={"request": request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def movements(self, request, pk=None):
        saving = self.get_object()
        movements = SavingMovement.objects.filter(saving=saving).order_by("-created_at")
        serializer = SavingMovementSerializer(movements, many=True)
        return Response(serializer.data)
