from rest_framework import serializers

from apps.categories.models import Category
from apps.income.models import Income


class IncomeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    amount_ars = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Income
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
            "created_at",
        ]
        read_only_fields = ["id", "amount_ars", "created_at"]

    def validate_category(self, category):
        user = self.context["request"].user
        from apps.core.constants import CategoryType

        allowed = Category.get_user_categories(user, CategoryType.INCOME)
        if category not in allowed:
            raise serializers.ValidationError("Categoría no válida para este usuario.")
        return category

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
