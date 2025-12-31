"""
Modelos para gestión de ahorro.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F

from apps.core.constants import Currency
from apps.core.mixins import SoftDeleteMixin, TimestampMixin


class SavingStatus(models.TextChoices):
    """Estados posibles de una meta de ahorro."""

    ACTIVE = "ACTIVE", "Activa"
    COMPLETED = "COMPLETED", "Completada"
    CANCELLED = "CANCELLED", "Cancelada"


class MovementType(models.TextChoices):
    """Tipos de movimiento de ahorro."""

    DEPOSIT = "DEPOSIT", "Depósito"
    WITHDRAWAL = "WITHDRAWAL", "Retiro"


class Saving(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Meta de ahorro del usuario.

    Hereda de:
    - TimestampMixin: created_at, updated_at
    - SoftDeleteMixin: is_active, deleted_at, soft_delete()
    """

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="savings", verbose_name="Usuario"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre de la meta")
    description = models.TextField(blank=True, verbose_name="Descripción")
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Monto objetivo",
    )
    current_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"), verbose_name="Monto actual"
    )
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=Currency.ARS, verbose_name="Moneda"
    )
    target_date = models.DateField(null=True, blank=True, verbose_name="Fecha objetivo")
    status = models.CharField(
        max_length=10,
        choices=SavingStatus.choices,
        default=SavingStatus.ACTIVE,
        verbose_name="Estado",
    )
    icon = models.CharField(max_length=50, default="bi-piggy-bank", verbose_name="Ícono")
    color = models.CharField(max_length=7, default="#17a2b8", verbose_name="Color")

    class Meta:
        verbose_name = "Meta de Ahorro"
        verbose_name_plural = "Metas de Ahorro"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.progress_percentage}%"

    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Validaciones del modelo."""
        super().clean()

        # Validar que el monto objetivo sea positivo
        if self.target_amount is not None and self.target_amount <= 0:
            raise ValidationError({"target_amount": "El monto objetivo debe ser mayor a cero."})

        # Validar que el monto actual no sea negativo
        if self.current_amount is not None and self.current_amount < 0:
            raise ValidationError({"current_amount": "El monto actual no puede ser negativo."})

    @property
    def progress_percentage(self):
        """Calcula el porcentaje de progreso."""
        if self.target_amount <= 0:
            return 0
        percentage = (self.current_amount / self.target_amount) * 100
        return min(round(percentage, 1), 100)  # Máximo 100%

    @property
    def remaining_amount(self):
        """Calcula el monto restante para alcanzar la meta."""
        remaining = self.target_amount - self.current_amount
        return max(remaining, Decimal("0.00"))

    @property
    def formatted_target(self):
        """Retorna el monto objetivo formateado."""
        symbol = "US$" if self.currency == Currency.USD else "$"
        return f"{symbol} {self.target_amount:,.2f}"

    @property
    def formatted_current(self):
        """Retorna el monto actual formateado."""
        symbol = "US$" if self.currency == Currency.USD else "$"
        return f"{symbol} {self.current_amount:,.2f}"

    @property
    def formatted_remaining(self):
        """Retorna el monto restante formateado."""
        symbol = "US$" if self.currency == Currency.USD else "$"
        return f"{symbol} {self.remaining_amount:,.2f}"

    @property
    def is_completed(self):
        """Indica si la meta fue completada."""
        return self.status == SavingStatus.COMPLETED

    @property
    def is_overdue(self):
        """Indica si la meta está vencida."""
        if not self.target_date:
            return False
        from django.utils import timezone

        return self.target_date < timezone.now().date() and self.status == SavingStatus.ACTIVE

    def add_deposit(self, amount, description=""):
        """
        Agrega un depósito a la meta de ahorro.

        Usa F() expressions para evitar race conditions.

        Args:
            amount: Monto a depositar
            description: Descripción opcional

        Returns:
            SavingMovement creado
        """
        if amount <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        # Crear el movimiento
        movement = SavingMovement.objects.create(
            saving=self, type=MovementType.DEPOSIT, amount=amount, description=description
        )

        # Actualizar current_amount usando F() para evitar race conditions
        Saving.objects.filter(pk=self.pk).update(current_amount=F("current_amount") + amount)

        # Refrescar la instancia para obtener el valor actualizado
        self.refresh_from_db()

        # Verificar si se completó la meta
        if self.current_amount >= self.target_amount and self.status == SavingStatus.ACTIVE:
            self.status = SavingStatus.COMPLETED
            self.save(update_fields=["status"])

        return movement

    def add_withdrawal(self, amount, description=""):
        """
        Agrega un retiro de la meta de ahorro.

        Usa F() expressions para evitar race conditions.

        Args:
            amount: Monto a retirar
            description: Descripción opcional

        Returns:
            SavingMovement creado

        Raises:
            ValueError: Si el monto es inválido o no hay suficiente saldo
        """
        if amount <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        # Refrescar para tener el valor más actualizado
        self.refresh_from_db()

        if amount > self.current_amount:
            raise ValueError("No hay suficiente saldo para este retiro.")

        # Crear el movimiento
        movement = SavingMovement.objects.create(
            saving=self, type=MovementType.WITHDRAWAL, amount=amount, description=description
        )

        # Actualizar current_amount usando F() para evitar race conditions
        Saving.objects.filter(pk=self.pk).update(current_amount=F("current_amount") - amount)

        # Refrescar la instancia para obtener el valor actualizado
        self.refresh_from_db()

        return movement

    @classmethod
    def get_user_savings(cls, user, status=None):
        """
        Obtiene las metas de ahorro de un usuario.

        Args:
            user: Usuario
            status: Estado opcional para filtrar

        Returns:
            QuerySet de metas de ahorro
        """
        queryset = cls.objects.filter(user=user)

        if status:
            queryset = queryset.filter(status=status)

        return queryset

    @classmethod
    def get_total_saved(cls, user):
        """
        Calcula el total ahorrado por un usuario (solo metas activas).

        Args:
            user: Usuario

        Returns:
            Decimal con el total
        """
        from django.db.models import Sum

        result = cls.objects.filter(
            user=user, status=SavingStatus.ACTIVE, is_active=True
        ).aggregate(total=Sum("current_amount"))

        return result["total"] or Decimal("0")


class SavingMovement(TimestampMixin, models.Model):
    """
    Movimiento de ahorro (depósito o retiro).
    """

    saving = models.ForeignKey(
        Saving, on_delete=models.CASCADE, related_name="movements", verbose_name="Meta de ahorro"
    )
    type = models.CharField(max_length=10, choices=MovementType.choices, verbose_name="Tipo")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Monto",
    )
    description = models.CharField(max_length=255, blank=True, verbose_name="Descripción")
    date = models.DateField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Movimiento de Ahorro"
        verbose_name_plural = "Movimientos de Ahorro"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        symbol = "+" if self.type == MovementType.DEPOSIT else "-"
        return f"{symbol} ${self.amount} - {self.saving.name}"

    @property
    def formatted_amount(self):
        """Retorna el monto formateado con signo."""
        symbol = "+" if self.type == MovementType.DEPOSIT else "-"
        return f"{symbol} ${self.amount:,.2f}"

    @property
    def is_deposit(self):
        """Indica si es un depósito."""
        return self.type == MovementType.DEPOSIT

    @property
    def is_withdrawal(self):
        """Indica si es un retiro."""
        return self.type == MovementType.WITHDRAWAL
