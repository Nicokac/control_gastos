from rest_framework import serializers

from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.recurring.models import RecurringExpense


class RecurringExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    installments_paid = serializers.IntegerField(read_only=True)
    installments_remaining = serializers.IntegerField(read_only=True)
    last_expense_amount = serializers.SerializerMethodField()
    last_expense_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = RecurringExpense
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "category_color",
            "due_day",
            "is_active",
            "notes",
            "total_installments",
            "starting_installment",
            "start_date",
            "installments_paid",
            "installments_remaining",
            "last_expense_amount",
            "last_expense_date",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "installments_paid",
            "installments_remaining",
            "last_expense_amount",
            "last_expense_date",
            "status",
            "created_at",
        ]

    def get_last_expense_amount(self, obj) -> str | None:
        last = obj.last_expense
        return str(last.amount_ars) if last else None

    def get_last_expense_date(self, obj) -> str | None:
        last = obj.last_expense
        return str(last.date) if last else None

    def get_status(self, obj) -> str:
        from django.utils import timezone

        today = timezone.localdate()
        return obj.status_for(today.month, today.year)

    def validate_category(self, category):
        user = self.context["request"].user
        allowed = Category.get_user_categories(user, CategoryType.EXPENSE)
        if category not in allowed:
            raise serializers.ValidationError("Categoría no válida para este usuario.")
        return category

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
