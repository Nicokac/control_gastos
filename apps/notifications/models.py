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
