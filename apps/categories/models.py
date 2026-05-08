"""Modelo Category para clasificar gastos e ingresos."""

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

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["type", "name"]
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

    @classmethod
    def get_user_categories(cls, user, category_type=None):
        """
        Obtiene las subcategorías disponibles para un usuario.
        Solo retorna subcategorías (parent != null) — los grupos no se asignan a transacciones.
        Incluye las del sistema y las propias del usuario.
        """
        queryset = cls.objects.filter(
            models.Q(is_system=True) | models.Q(user=user),
            parent__isnull=False,
        )

        if category_type:
            queryset = queryset.filter(type=category_type)

        return queryset.select_related("parent").order_by("parent__name", "name")

    @classmethod
    def get_expense_categories(cls, user):
        """Obtiene subcategorías de tipo EXPENSE para un usuario."""
        return cls.get_user_categories(user, CategoryType.EXPENSE)

    @classmethod
    def get_income_categories(cls, user):
        """Obtiene subcategorías de tipo INCOME para un usuario."""
        return cls.get_user_categories(user, CategoryType.INCOME)

    @classmethod
    def get_groups(cls, user, category_type=None):
        """Obtiene los grupos disponibles para un usuario (sistema + propios)."""
        queryset = cls.objects.filter(
            models.Q(is_system=True) | models.Q(user=user),
            parent__isnull=True,
        )
        if category_type:
            queryset = queryset.filter(type=category_type)
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
