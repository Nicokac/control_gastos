from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class User(AbstractUser):
    """Custom user model with finance preferences."""

    class Currency(models.TextChoices):
        ARS = 'ARS', 'Peso Argentino'
        USD = 'USD', 'Dólar Estadoudinense'

    email = models.EmailField(unique=True)
    default_currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.ARS,
        verbose_name='Moneda principal'
    )
    alert_threshold = models.IntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Umbral de alerta (%)'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.email