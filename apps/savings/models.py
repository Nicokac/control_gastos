"""
Modelos para gestión de ahorro.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

from apps.core.constants import Currency
from apps.core.mixins import TimestampMixin
from apps.core.utils import format_currency


class SavingStatus(models.TextChoices):
    """Estados posibles de una meta de ahorro."""

    ACTIVE = "ACTIVE", "Activa"
    COMPLETED = "COMPLETED", "Completada"
    CANCELLED = "CANCELLED", "Cancelada"


class MovementType(models.TextChoices):
    """Tipos de movimiento de ahorro."""

    DEPOSIT = "DEPOSIT", "Depósito"
    WITHDRAWAL = "WITHDRAWAL", "Retiro"


class RolloverSuggestionStatus(models.TextChoices):
    """Estados posibles de una sugerencia de traslado de sobrante (DT-067)."""

    PENDING = "PENDING", "Pendiente"
    DEPOSITED = "DEPOSITED", "Destinado a meta"
    DISMISSED = "DISMISSED", "Descartado"


class Saving(TimestampMixin, models.Model):
    """
    Meta de ahorro del usuario.

    Hereda de:
    - TimestampMixin: created_at, updated_at
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
    color = models.CharField(max_length=7, default="#28a745", verbose_name="Color")

    class Meta:
        verbose_name = "Meta de Ahorro"
        verbose_name_plural = "Metas de Ahorro"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(target_amount__gt=0),
                name="saving_target_amount_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(current_amount__gte=0),
                name="saving_current_amount_non_negative",
            ),
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
        return format_currency(self.target_amount, self.currency)

    @property
    def formatted_current(self):
        """Retorna el monto actual formateado."""
        return format_currency(self.current_amount, self.currency)

    @property
    def formatted_remaining(self):
        """Retorna el monto restante formateado."""
        return format_currency(self.remaining_amount, self.currency)

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

        return self.target_date < timezone.localdate() and self.status == SavingStatus.ACTIVE

    def add_deposit(self, amount, description=""):
        """
        Agrega un depósito a la meta de ahorro.

        Usa select_for_update + transaction.atomic para evitar race conditions
        en la verificación de compleción.

        Args:
            amount: Monto a depositar
            description: Descripción opcional

        Returns:
            SavingMovement creado
        """
        if amount <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        with transaction.atomic():
            # Bloquear el registro para evitar race conditions en la verificación de compleción
            saving = Saving.objects.select_for_update().get(pk=self.pk)

            # Crear el movimiento
            movement = SavingMovement.objects.create(
                saving=saving, type=MovementType.DEPOSIT, amount=amount, description=description
            )
            # Actualizar current_amount usando F() para evitar race conditions
            Saving.objects.filter(pk=self.pk).update(current_amount=F("current_amount") + amount)
            # Refrescar la instancia para obtener el valor actualizado
            saving.refresh_from_db()

            # Verificar si se completó la meta
            if (
                saving.current_amount >= saving.target_amount
                and saving.status == SavingStatus.ACTIVE
            ):
                saving.status = SavingStatus.COMPLETED
                saving.save(update_fields=["status"])

            # Sincronizar self con los valores actualizados
            self.current_amount = saving.current_amount
            self.status = saving.status

        return movement

    def add_withdrawal(self, amount, description=""):
        """
        Agrega un retiro de la meta de ahorro.

        Usa select_for_update + transaction.atomic para evitar race conditions.

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

        with transaction.atomic():
            # Bloquear el registro para evitar race conditions (SELECT FOR UPDATE)
            locked_saving = Saving.objects.select_for_update().get(pk=self.pk)

            if amount > locked_saving.current_amount:
                raise ValueError("No hay suficiente saldo para este retiro.")

            # Crear el movimiento
            movement = SavingMovement.objects.create(
                saving=self, type=MovementType.WITHDRAWAL, amount=amount, description=description
            )

            # Actualizar current_amount usando F() para operación atómica
            Saving.objects.filter(pk=self.pk).update(current_amount=F("current_amount") - amount)

        # Refrescar la instancia para obtener el valor actualizado
        self.refresh_from_db()

        return movement


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
        indexes = [
            models.Index(fields=["saving", "-date", "-created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="saving_movement_amount_positive",
            )
        ]

    def __str__(self):
        symbol = "+" if self.type == MovementType.DEPOSIT else "-"
        return f"{symbol} ${self.amount} - {self.saving.name}"

    @property
    def formatted_amount(self):
        sign = "+" if self.type == MovementType.DEPOSIT else "-"
        formatted = f"{self.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{sign} $ {formatted}"

    @property
    def is_deposit(self):
        """Indica si es un depósito."""
        return self.type == MovementType.DEPOSIT

    @property
    def is_withdrawal(self):
        """Indica si es un retiro."""
        return self.type == MovementType.WITHDRAWAL


class RolloverSuggestion(TimestampMixin, models.Model):
    """
    Sugerencia de traslado del sobrante de un período financiero cerrado (DT-067).

    Se crea en estado PENDING cuando el usuario entra al dashboard y el período
    financiero inmediatamente anterior cerró con balance positivo. El usuario
    decide si lo destina a una meta de ahorro (DEPOSITED) o lo descarta
    (DISMISSED, el dinero queda disponible para gastar en el período actual).
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="rollover_suggestions",
        verbose_name="Usuario",
    )
    period_start = models.DateField(verbose_name="Inicio del período")
    period_end = models.DateField(verbose_name="Fin del período (exclusivo)")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Monto del sobrante",
    )
    status = models.CharField(
        max_length=10,
        choices=RolloverSuggestionStatus.choices,
        default=RolloverSuggestionStatus.PENDING,
        verbose_name="Estado",
    )
    saving = models.ForeignKey(
        Saving,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rollover_suggestions",
        verbose_name="Meta destino",
    )
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Resuelto el")

    class Meta:
        verbose_name = "Sugerencia de Traslado de Sobrante"
        verbose_name_plural = "Sugerencias de Traslado de Sobrante"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "period_start", "period_end"],
                name="rollover_suggestion_unique_period",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="rollover_suggestion_amount_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(period_end__gt=models.F("period_start")),
                name="rollover_suggestion_end_after_start",
            ),
        ]

    def __str__(self):
        return (
            f"{self.user} - {self.period_start} a {self.period_end} - {self.get_status_display()}"
        )

    def clean(self):
        """Validaciones del modelo."""
        super().clean()

        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "El monto del sobrante debe ser mayor a cero."})

        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_end <= self.period_start
        ):
            raise ValidationError(
                {"period_end": "El fin del período debe ser posterior al inicio."}
            )

        if self.status == RolloverSuggestionStatus.DEPOSITED and self.saving_id is None:
            raise ValidationError(
                {"saving": "Una sugerencia destinada a una meta debe indicar la meta."}
            )

    @property
    def formatted_amount(self):
        return format_currency(self.amount)

    @property
    def is_pending(self):
        return self.status == RolloverSuggestionStatus.PENDING

    def mark_dismissed(self):
        """Descarta la sugerencia: el usuario decidió gastar el sobrante en el período actual."""
        self.status = RolloverSuggestionStatus.DISMISSED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

    def mark_deposited(self, saving):
        """Marca la sugerencia como destinada a una meta de ahorro."""
        self.status = RolloverSuggestionStatus.DEPOSITED
        self.saving = saving
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "saving", "resolved_at", "updated_at"])
