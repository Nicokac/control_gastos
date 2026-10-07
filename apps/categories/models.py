"""Modelo Category para clasificar gastos e ingresos."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.constants import CategoryType
from apps.core.mixins import TimestampMixin


# Create your models here.
class Category(TimestampMixin, models.Model):
    """
    Categoría para clasificar gastos e ingresos.

    Puede ser:
    - Del sistema (is_system=True): Predefinidos, no editables por usuarios
    - De usuario (is_system=False): Creadas por cada usuario
    """

    name = models.CharField(max_length=100, verbose_name="Nombre")
    type = models.CharField(max_length=10, choices=CategoryType.choices, verbose_name="Tipo")
    is_system = models.BooleanField(default=False, verbose_name="Categoría del sistema")
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories",
        verbose_name="Usuario",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name="Grupo",
        help_text="Grupo al que pertenece esta subcategoría. Vacío = es un grupo.",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Posición del grupo en la lista (solo aplica a grupos).",
    )
    icon = models.CharField(
        max_length=50,
        default="bi-tag",
        blank=True,
        verbose_name="Ícono",
        help_text="Nombre del ícono de Bootstrap Icons (ej: bi-cart)",
    )
    color = models.CharField(
        max_length=7,
        default="#6c757d",
        blank=True,
        verbose_name="Color",
        help_text="Color hexadecimal (ej: #28a745)",
    )
    monthly_alert_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Umbral de alerta mensual",
        help_text="Avisa cuando el gasto del mes en esta subcategoría supera este monto. Solo aplica a subcategorías de gasto.",
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["type", "order", "name"]
        constraints = [
            # Grupos: nombre único por usuario y tipo dentro de los grupos (parent IS NULL)
            models.UniqueConstraint(
                fields=["name", "user", "type"],
                condition=models.Q(parent__isnull=True),
                name="unique_group_name_per_user_and_type",
            ),
            # Subcategorías: nombre único por usuario, tipo y grupo padre
            models.UniqueConstraint(
                fields=["name", "user", "type", "parent"],
                condition=models.Q(parent__isnull=False),
                name="unique_subcategory_name_per_user_type_and_parent",
            ),
            # Categorías del sistema no pueden tener usuario
            models.CheckConstraint(
                condition=~models.Q(is_system=True, user__isnull=False),
                name="system_category_no_user",
            ),
            models.CheckConstraint(
                condition=~models.Q(is_system=False, user__isnull=True),
                name="user_category_requires_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "type"]),
            models.Index(fields=["is_system", "type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Validaciones del módelo."""
        super().clean()

        # Si es categoría del sistema, user debe ser null
        if self.is_system and self.user is not None:
            raise ValidationError(
                {"user": "Las categorías del sistema no pueden tener usuario asignado."}
            )

        # Si no es del sistema, debe tener usuario
        if not self.is_system and self.user is None:
            raise ValidationError(
                {"user": "Las categorías personalizadas deben tener un usuario asignado."}
            )

        # El parent no puede ser una subcategoría (máximo 2 niveles)
        if self.parent_id is not None:
            if self.parent.parent_id is not None:
                raise ValidationError(
                    {
                        "parent": "No se puede asignar una subcategoría como grupo (máximo 2 niveles)."
                    }
                )
            # El parent debe ser del mismo tipo
            if self.parent.type != self.type:
                raise ValidationError(
                    {"parent": "El grupo debe ser del mismo tipo que la subcategoría."}
                )

        # Una categoría no puede ser su propio padre
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({"parent": "Una categoría no puede ser su propio grupo."})

        # El umbral de alerta solo tiene sentido en subcategorías de gasto
        if self.monthly_alert_threshold is not None:
            if self.type != CategoryType.EXPENSE:
                raise ValidationError(
                    {
                        "monthly_alert_threshold": "El umbral de alerta solo aplica a categorías de gasto."
                    }
                )
            if self.is_group:
                raise ValidationError(
                    {
                        "monthly_alert_threshold": "El umbral de alerta solo aplica a subcategorías, no a grupos."
                    }
                )

    @property
    def is_group(self):
        """Verdadero si es un grupo (sin parent)."""
        return self.parent_id is None

    @property
    def is_subcategory(self):
        """Verdadero si es una subcategoría (tiene parent)."""
        return self.parent_id is not None

    @property
    def is_editable(self):
        """Indica si la categoría puede ser editada."""
        return not self.is_system

    @property
    def is_deletable(self):
        """Indica si la categoría puede ser eliminada."""
        return not self.is_system

    def current_month_spent(self, user):
        """Total gastado por `user` en esta subcategoría durante el mes
        en curso. El umbral es por categoría pero el gasto es por usuario
        (una subcategoría de sistema puede estar compartida)."""
        from django.db.models import Sum
        from django.utils import timezone

        from apps.core.utils import get_month_date_range_exclusive

        today = timezone.localdate()
        start, end = get_month_date_range_exclusive(today.month, today.year)
        result = self.expenses.filter(user=user, date__gte=start, date__lt=end).aggregate(
            total=Sum("amount_ars")
        )
        return result["total"] or Decimal("0")

    def is_over_alert_threshold(self, user):
        """Verdadero si el gasto del mes en curso ya superó el umbral configurado."""
        if self.monthly_alert_threshold is None:
            return False
        return self.current_month_spent(user) >= self.monthly_alert_threshold

    @classmethod
    def _exclude_hidden(cls, queryset, user):
        """Excluye categorías de sistema que el usuario ocultó (DT-086)."""
        hidden_ids = CategoryOverride.objects.filter(user=user, is_hidden=True).values_list(
            "category_id", flat=True
        )
        return queryset.exclude(pk__in=hidden_ids)

    @classmethod
    def get_user_categories(cls, user, category_type=None):
        """
        Obtiene las subcategorías disponibles para un usuario.
        Solo retorna subcategorías (parent != null) — los grupos no se asignan a transacciones.
        Incluye las del sistema y las propias del usuario, excepto las que el
        usuario haya ocultado.
        """
        queryset = cls.objects.filter(
            models.Q(is_system=True) | models.Q(user=user),
            parent__isnull=False,
        )

        if category_type:
            queryset = queryset.filter(type=category_type)

        queryset = cls._exclude_hidden(queryset, user)
        return queryset.select_related("parent").order_by("parent__name", "name")

    @classmethod
    def get_expense_categories(cls, user):
        """Obtiene subcategorías de tipo EXPENSE para un usuario."""
        return cls.get_user_categories(user, CategoryType.EXPENSE)

    @classmethod
    def get_income_categories(cls, user):
        """
        Obtiene categorías de tipo INCOME para un usuario.
        Incluye tanto grupos como subcategorías porque los ingresos del sistema
        son de un solo nivel (no tienen parent), excepto las que el usuario
        haya ocultado.
        """
        queryset = cls.objects.filter(
            models.Q(is_system=True) | models.Q(user=user),
            type=CategoryType.INCOME,
        )
        queryset = cls._exclude_hidden(queryset, user)
        return queryset.select_related("parent").order_by("parent__name", "name")

    @classmethod
    def get_groups(cls, user, category_type=None):
        """Obtiene los grupos disponibles para un usuario (sistema + propios),
        excepto los que el usuario haya ocultado."""
        queryset = cls.objects.filter(
            models.Q(is_system=True) | models.Q(user=user),
            parent__isnull=True,
        )
        if category_type:
            queryset = queryset.filter(type=category_type)
        queryset = cls._exclude_hidden(queryset, user)
        return queryset.order_by("name")

    @classmethod
    def get_categories_by_group(cls, user, category_type):
        """
        Retorna lista de (grupo, [subcategorías]) para armar un selector agrupado.
        Solo incluye grupos que tengan al menos una subcategoría disponible.
        """
        subcategories = cls.get_user_categories(user, category_type).select_related("parent")
        groups: dict = {}
        for sub in subcategories:
            group = sub.parent
            if group.pk not in groups:
                groups[group.pk] = {"group": group, "subcategories": []}
            groups[group.pk]["subcategories"].append(sub)
        return list(groups.values())


class CategoryOverride(TimestampMixin, models.Model):
    """
    Preferencia de un usuario sobre una categoría de SISTEMA, sin modificar
    la categoría compartida (que afectaría a todos los usuarios). Hoy solo
    soporta ocultarla de los selectores de creación — no afecta gastos/
    ingresos ya cargados con esa categoría (DT-086).
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="category_overrides",
        verbose_name="Usuario",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="user_overrides",
        verbose_name="Categoría",
    )
    is_hidden = models.BooleanField(default=False, verbose_name="Oculta")

    class Meta:
        verbose_name = "Preferencia de categoría"
        verbose_name_plural = "Preferencias de categoría"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category"], name="unique_override_per_user_and_category"
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.category} (oculta={self.is_hidden})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.category_id and not self.category.is_system:
            raise ValidationError(
                {"category": "Solo se puede personalizar una categoría del sistema."}
            )
