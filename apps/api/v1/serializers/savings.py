from decimal import Decimal

from rest_framework import serializers

from apps.savings.models import Saving, SavingMovement


class SavingMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingMovement
        fields = ["id", "type", "amount", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class SavingSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.FloatField(read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Saving
        fields = [
            "id",
            "name",
            "description",
            "target_amount",
            "current_amount",
            "currency",
            "target_date",
            "status",
            "icon",
            "color",
            "progress_percentage",
            "remaining_amount",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "current_amount",
            "progress_percentage",
            "remaining_amount",
            "created_at",
        ]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class DepositWithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    description = serializers.CharField(max_length=255, required=False, default="")
