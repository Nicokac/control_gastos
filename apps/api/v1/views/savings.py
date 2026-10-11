from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.v1.pagination import ConfigurablePageNumberPagination
from apps.api.v1.serializers.savings import (
    DepositWithdrawSerializer,
    RolloverDepositSerializer,
    RolloverSuggestionSerializer,
    SavingMovementSerializer,
    SavingSerializer,
)
from apps.savings.models import (
    RolloverSuggestion,
    RolloverSuggestionStatus,
    Saving,
    SavingMovement,
    SavingStatus,
)


class SavingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SavingSerializer
    pagination_class = ConfigurablePageNumberPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Saving.objects.none()
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


class RolloverSuggestionViewSet(viewsets.GenericViewSet):
    """Acciones sobre sugerencias de traslado de sobrante (DT-067)."""

    permission_classes = [IsAuthenticated]
    serializer_class = RolloverSuggestionSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return RolloverSuggestion.objects.none()
        return RolloverSuggestion.objects.filter(user=self.request.user)

    def get_pending_object(self):
        return get_object_or_404(
            self.get_queryset(), pk=self.kwargs["pk"], status=RolloverSuggestionStatus.PENDING
        )

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        suggestion = self.get_pending_object()
        suggestion.mark_dismissed()
        return Response(RolloverSuggestionSerializer(suggestion).data)

    @action(detail=True, methods=["post"])
    def deposit(self, request, pk=None):
        suggestion = self.get_pending_object()
        serializer = RolloverDepositSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        saving = get_object_or_404(
            Saving,
            pk=serializer.validated_data["saving_id"],
            user=request.user,
            status=SavingStatus.ACTIVE,
        )
        saving.add_deposit(
            suggestion.amount, description=f"Sobrante de {suggestion.period_start:%B %Y}"
        )
        suggestion.mark_deposited(saving)
        return Response(RolloverSuggestionSerializer(suggestion).data)
