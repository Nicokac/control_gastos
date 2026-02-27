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
            models.UniqueConstraint(
                fields=["name", "user", "type"], name="unique_category_per_user_and_type"
            ),
            # Categorías del sistema no pueden tener usuario
            models.CheckConstraint(
                check=~models.Q(is_system=True, user__isnull=False),
                name="system_category_no_user",
            ),
            # Categorías de usuario deben tener usuario
            models.CheckConstraint(
                check=~models.Q(is_system=False, user__isnull=True),
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

    @property
    def is_editable(self):
        """Indica si la categoría puede ser editada."""
        return not self.is_system

    @property
    def is_deletable(self):
        """Indica si la categoría puede ser eliminada,"""
        return not self.is_system

    @classmethod
    def get_user_categories(cls, user, category_type=None):
        """
        Obtiene las categorías disponibles para un usuario.
        Incluye las del sistema y las propias del usuario.

        Args:
            user: Usuario
            category_type: Filtrar por tipo (EXPENSE/INCOME)

        Returns:
            QuerySet de categorías
        """
        queryset = cls.objects.filter(models.Q(is_system=True) | models.Q(user=user))

        if category_type:
            queryset = queryset.filter(type=category_type)

        return queryset.order_by("type", "name")

    @classmethod
    def get_expense_categories(cls, user):
        """Obtiene categorías de tipo EXPENSE para un usuario."""
        return cls.get_user_categories(user, CategoryType.EXPENSE)

    @classmethod
    def get_income_categories(cls, user):
        """Obtiene categorías de tipo INCOME para un usuario."""
        return cls.get_user_categories(user, CategoryType.INCOME)
