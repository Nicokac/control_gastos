from rest_framework import serializers

from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.recurring_income.models import RecurringIncome


class RecurringIncomeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    last_income_amount = serializers.SerializerMethodField()
    last_income_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = RecurringIncome
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "category_color",
            "expected_day",
            "is_active",
            "notes",
            "last_income_amount",
            "last_income_date",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "last_income_amount",
            "last_income_date",
            "status",
            "created_at",
        ]

    def get_last_income_amount(self, obj):
        last = obj.last_income
        return str(last.amount_ars) if last else None

    def get_last_income_date(self, obj):
        last = obj.last_income
        return str(last.date) if last else None

    def get_status(self, obj):
        from django.utils import timezone

        today = timezone.localdate()
        return obj.status_for(today.month, today.year)

    def validate_category(self, category):
        user = self.context["request"].user
        allowed = Category.get_user_categories(user, CategoryType.INCOME)
        if category not in allowed:
            raise serializers.ValidationError("Categoría no válida para este usuario.")
        return category

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
