"""
Modelos para notificaciones push (Firebase Cloud Messaging).
"""

from django.db import models

from apps.core.mixins import TimestampMixin


class DevicePlatform(models.TextChoices):
    """Plataforma del dispositivo que registra el token."""

    ANDROID = "ANDROID", "Android"
    IOS = "IOS", "iOS"


class DeviceToken(TimestampMixin, models.Model):
    """
    Token FCM de un dispositivo mobile, para poder enviarle notificaciones
    push. Un usuario puede tener varios dispositivos (celular, tablet).

    El token es único a nivel global (no por usuario): Firebase puede
    reasignar el mismo token a una instalación distinta si la anterior se
    desinstaló, así que al registrar un token que ya existía para otro
    usuario, se reasigna en vez de fallar por duplicado.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="device_tokens",
        verbose_name="Usuario",
    )
    token = models.CharField(max_length=255, unique=True, verbose_name="Token FCM")
    platform = models.CharField(
        max_length=10,
        choices=DevicePlatform.choices,
        default=DevicePlatform.ANDROID,
        verbose_name="Plataforma",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Se desactiva automáticamente si Firebase reporta el token como inválido.",
    )
    last_used_at = models.DateTimeField(auto_now=True, verbose_name="Último registro/actualización")

    class Meta:
        verbose_name = "Token de dispositivo"
        verbose_name_plural = "Tokens de dispositivo"
        ordering = ["-last_used_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.platform} ({self.token[:12]}...)"


class ReminderKind(models.TextChoices):
    DUE_SOON = "due_soon", "Por vencer"
    OVERDUE = "overdue", "Vencido sin pagar"


class RecurringReminderLog(TimestampMixin, models.Model):
    """Recordatorio ya enviado para un gasto fijo, una fecha de vencimiento y un tipo de aviso.

    La unicidad evita reenviar el mismo aviso si el cron diario se ejecuta más de una vez.
    """

    recurring = models.ForeignKey(
        "recurring.RecurringExpense",
        on_delete=models.CASCADE,
        related_name="reminder_logs",
        verbose_name="Gasto fijo",
    )
    due_date = models.DateField(verbose_name="Fecha de vencimiento")
    kind = models.CharField(
        max_length=20,
        choices=ReminderKind.choices,
        default=ReminderKind.DUE_SOON,
        verbose_name="Tipo de aviso",
    )

    class Meta:
        verbose_name = "Recordatorio enviado"
        verbose_name_plural = "Recordatorios enviados"
        ordering = ["-due_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["recurring", "due_date", "kind"],
                name="unique_reminder_per_recurring_due_date_kind",
            ),
        ]

    def __str__(self):
        return f"{self.recurring} - {self.due_date} ({self.get_kind_display()})"


class NotificationType(models.TextChoices):
    RECURRING_REMINDER = "recurring_reminder", "Recordatorio de gastos fijos"
    RECURRING_OVERDUE = "recurring_overdue", "Gastos fijos vencidos sin pagar"
    SPENDING_THRESHOLD = "spending_threshold", "Umbral de gastos del período superado"
    CATEGORY_THRESHOLD = "category_threshold", "Límite de subcategoría superado"


class Notification(TimestampMixin, models.Model):
    """Aviso enviado al usuario, para el historial de la campanita en mobile.

    Se guarda aparte del push porque el del sistema desaparece apenas el usuario lo descarta.
    """

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Usuario",
    )
    type = models.CharField(max_length=40, choices=NotificationType.choices, verbose_name="Tipo")
    title = models.CharField(max_length=120, verbose_name="Título")
    body = models.TextField(verbose_name="Texto")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Leída el")

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "read_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"


class SpendingAlertKind(models.TextChoices):
    GLOBAL = "global", "Umbral del período"
    CATEGORY = "category", "Límite de subcategoría"


class SpendingAlertLog(TimestampMixin, models.Model):
    """Alerta de gastos ya enviada, para avisar una sola vez por período (y por subcategoría)."""

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="spending_alert_logs",
        verbose_name="Usuario",
    )
    kind = models.CharField(max_length=20, choices=SpendingAlertKind.choices, verbose_name="Tipo")
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="spending_alert_logs",
        verbose_name="Subcategoría",
    )
    period_start = models.DateField(verbose_name="Inicio del período")

    class Meta:
        verbose_name = "Alerta de gastos enviada"
        verbose_name_plural = "Alertas de gastos enviadas"
        ordering = ["-period_start"]
        # Dos restricciones condicionales: en una única con `category` nula, NULL no se
        # considera repetido y la alerta global podría registrarse dos veces.
        constraints = [
            models.UniqueConstraint(
                fields=["user", "period_start"],
                condition=models.Q(kind="global"),
                name="unique_global_spending_alert_per_period",
            ),
            models.UniqueConstraint(
                fields=["user", "category", "period_start"],
                condition=models.Q(kind="category"),
                name="unique_category_spending_alert_per_period",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_kind_display()} ({self.period_start})"
