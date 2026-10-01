from rest_framework import serializers

from apps.categories.models import Category
from apps.core.constants import CategoryType


class CategoryGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "type", "icon", "color", "order", "is_system"]


class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source="parent.name", read_only=True)

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
        ]
        read_only_fields = ["id", "is_system"]

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
