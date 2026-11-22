from rest_framework import serializers

from apps.categories.models import Category, CategoryOverride, CategoryRule
from apps.categories.rules import normalize_text
from apps.core.constants import CategoryType


class CategoryRuleSerializer(serializers.ModelSerializer):
    """Mismas validaciones que CategoryRuleForm (web)."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    group_name = serializers.CharField(source="category.parent.name", read_only=True)

    class Meta:
        model = CategoryRule
        fields = ["id", "pattern", "category", "category_name", "group_name"]
        read_only_fields = ["id"]

    def validate_pattern(self, value):
        pattern = normalize_text(value)
        if not pattern:
            raise serializers.ValidationError("Escribí al menos una palabra.")
        duplicates = CategoryRule.objects.filter(user=self.context["request"].user, pattern=pattern)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("Ya tenés una regla con ese texto.")
        return pattern

    def validate_category(self, category):
        user = self.context["request"].user
        if not Category.get_expense_categories(user).filter(pk=category.pk).exists():
            raise serializers.ValidationError("Elegí una subcategoría de gasto.")
        return category

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class CategoryGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type", "icon", "color", "order", "is_system"]


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    is_hidden = serializers.SerializerMethodField()
    current_month_spent = serializers.SerializerMethodField()
    is_over_alert_threshold = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "type",
            "icon",
            "color",
            "is_system",
            "parent",
            "parent_name",
            "is_hidden",
            "monthly_alert_threshold",
            "current_month_spent",
            "is_over_alert_threshold",
        ]
        read_only_fields = [
            "id",
            "is_system",
            "current_month_spent",
            "is_over_alert_threshold",
        ]

    def _request_user(self):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user
        return None

    def _override(self, obj):
        # Una sola consulta por pedido, compartida por todas las categorías del listado.
        if "_overrides" not in self.context:
            user = self._request_user()
            self.context["_overrides"] = (
                {o.category_id: o for o in CategoryOverride.objects.filter(user=user)}
                if user
                else {}
            )
        return self.context["_overrides"].get(obj.pk)

    def _threshold(self, obj):
        if not obj.is_system:
            return obj.monthly_alert_threshold
        override = self._override(obj)
        return override.monthly_alert_threshold if override else None

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if obj.is_system:
            # En las del sistema el límite es el de cada usuario (DT-120).
            threshold = self._threshold(obj)
            data["monthly_alert_threshold"] = (
                None
                if threshold is None
                else self.fields["monthly_alert_threshold"].to_representation(threshold)
            )
        return data

    def get_is_hidden(self, obj) -> bool:
        if not obj.is_system:
            return False
        override = self._override(obj)
        return bool(override and override.is_hidden)

    def get_current_month_spent(self, obj) -> str | None:
        user = self._request_user()
        if user is None or self._threshold(obj) is None:
            return None
        return str(obj.current_month_spent(user))

    def get_is_over_alert_threshold(self, obj) -> bool:
        user = self._request_user()
        threshold = self._threshold(obj)
        if user is None or threshold is None:
            return False
        return obj.current_month_spent(user) >= threshold

    def validate(self, attrs):
        user = self.context["request"].user
        parent = attrs.get("parent")
        category_type = attrs.get("type")

        if parent and parent.type != category_type:
            raise serializers.ValidationError(
                {"parent": "El grupo debe ser del mismo tipo que la subcategoría."}
            )
        if parent and parent.parent is not None:
            raise serializers.ValidationError({"parent": "No se puede anidar más de dos niveles."})

        threshold = attrs.get("monthly_alert_threshold")
        if threshold is not None:
            if category_type != CategoryType.EXPENSE:
                raise serializers.ValidationError(
                    {
                        "monthly_alert_threshold": "El umbral de alerta solo aplica a categorías de gasto."
                    }
                )
            if parent is None:
                raise serializers.ValidationError(
                    {
                        "monthly_alert_threshold": "El umbral de alerta solo aplica a subcategorías, no a grupos."
                    }
                )

        name = attrs.get("name", "")
        qs = Category.objects.filter(name__iexact=name, user=user, type=category_type)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({"name": "Ya tenés una categoría con este nombre."})

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        validated_data["is_system"] = False
        instance = super().create(validated_data)

        # Los gastos solo pueden asignarse a subcategorías (ver D-011), así que un
        # grupo de gastos recién creado sin subcategorías quedaría invisible al cargar
        # un gasto. Los ingresos no tienen esta restricción. Ver CategoryCreateView
        # (web) para la misma lógica.
        if instance.parent_id is None and instance.type == CategoryType.EXPENSE:
            Category.objects.create(
                name="General",
                type=instance.type,
                user=instance.user,
                parent=instance,
                color=instance.color,
                icon=instance.icon,
            )

        return instance
