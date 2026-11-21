from rest_framework import serializers

from apps.categories.models import Category
from apps.core.constants import CategoryType
from apps.recurring.detection import find_suggestion, link_suggestion_expenses
from apps.recurring.models import RecurringExpense


class RecurringExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    installments_paid = serializers.IntegerField(read_only=True)
    installments_remaining = serializers.IntegerField(read_only=True)
    last_expense_amount = serializers.SerializerMethodField()
    last_expense_date = serializers.SerializerMethodField()
    display_amount = serializers.SerializerMethodField()
    is_estimated_amount = serializers.BooleanField(read_only=True)
    status = serializers.SerializerMethodField()
    suggestion = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Clave de la sugerencia de gasto fijo (DT-053): al crear, vincula sus pagos.",
    )

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
            "estimated_amount",
            "is_auto_debit",
            "installments_paid",
            "installments_remaining",
            "last_expense_amount",
            "last_expense_date",
            "display_amount",
            "is_estimated_amount",
            "status",
            "created_at",
            "suggestion",
        ]
        read_only_fields = [
            "id",
            "installments_paid",
            "installments_remaining",
            "last_expense_amount",
            "last_expense_date",
            "display_amount",
            "is_estimated_amount",
            "status",
            "created_at",
        ]

    def get_last_expense_amount(self, obj) -> str | None:
        last = obj.last_expense
        return str(last.amount_ars) if last else None

    def get_last_expense_date(self, obj) -> str | None:
        last = obj.last_expense
        return str(last.date) if last else None

    def get_display_amount(self, obj) -> str | None:
        amount = obj.display_amount
        return str(amount) if amount is not None else None

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
        key = validated_data.pop("suggestion", "")
        user = self.context["request"].user
        suggestion = find_suggestion(user, key) if key else None
        validated_data["user"] = user
        recurring = super().create(validated_data)
        if suggestion:
            link_suggestion_expenses(suggestion, recurring)
        return recurring

    def update(self, instance, validated_data):
        validated_data.pop("suggestion", None)
        return super().update(instance, validated_data)


class RecurringSuggestionSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    category = serializers.IntegerField(source="category.pk")
    category_name = serializers.CharField(source="category.name")
    group_name = serializers.CharField(source="category.parent.name", default=None)
    due_day = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    months = serializers.IntegerField()
    expense_count = serializers.SerializerMethodField()

    def get_expense_count(self, obj) -> int:
        return len(obj.expense_ids)
