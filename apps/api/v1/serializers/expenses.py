from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.categories.models import Category
from apps.expenses.models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    amount_ars = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id",
            "date",
            "description",
            "amount",
            "currency",
            "exchange_rate",
            "amount_ars",
            "category",
            "category_name",
            "category_color",
            "category_icon",
            "payment_method",
            "saving",
            "recurring",
            "created_at",
        ]
        read_only_fields = ["id", "amount_ars", "created_at"]

    def validate_category(self, category):
        user = self.context["request"].user
        allowed = Category.get_user_categories(user)
        if category not in allowed:
            raise serializers.ValidationError("Categoría no válida para este usuario.")
        return category

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict) from e
