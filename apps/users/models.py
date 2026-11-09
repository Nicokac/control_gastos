from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.constants import Currency


# Create your models here.
class User(AbstractUser):
    """Custom user model with finance preferences."""

    email = models.EmailField(unique=True)
    default_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.ARS,
        verbose_name="Moneda principal",
    )
    alert_threshold = models.IntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="Umbral de alerta (%)",
    )
    financial_month_start_day = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name="Inicio del mes financiero",
        help_text="Día del mes en que empieza tu período financiero (ej: día que cobrás el sueldo). Rango: 1-28.",
    )
    email_verified = models.BooleanField(default=False, verbose_name="Email verificado")
    has_seen_tour = models.BooleanField(default=False, verbose_name="Tour visto")
    recurring_reminders_enabled = models.BooleanField(
        default=True,
        verbose_name="Recordatorios de gastos fijos",
        help_text="Aviso push en mobile 3 días antes del vencimiento de cada gasto fijo.",
    )
    spending_alerts_enabled = models.BooleanField(
        default=True,
        verbose_name="Alertas de gastos",
        help_text="Aviso push en mobile al superar el umbral de gastos del período o el límite de una subcategoría.",
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email
