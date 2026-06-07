from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.categories.models import Category
from apps.shared_expenses.models import HouseholdMember, SharedExpense


class HouseholdMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseholdMember
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        user = self.context["request"].user
        qs = HouseholdMember.objects.filter(user=user, name__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya tenés un miembro con ese nombre.")
        return value

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class SharedExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    paid_by_name = serializers.SerializerMethodField()
    amount_ars = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = SharedExpense
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
            "paid_by",
            "paid_by_name",
            "created_at",
        ]
        read_only_fields = ["id", "amount_ars", "created_at"]

    def get_paid_by_name(self, obj) -> str | None:
        return obj.paid_by.name if obj.paid_by else None

    def validate_category(self, category):
        user = self.context["request"].user
        allowed = Category.get_user_categories(user)
        if category not in allowed:
            raise serializers.ValidationError("Categoría no válida para este usuario.")
        return category

    def validate_paid_by(self, member):
        if member is None:
            return member
        user = self.context["request"].user
        if member.user != user:
            raise serializers.ValidationError("El miembro no pertenece a tu hogar.")
        return member

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict) from e
