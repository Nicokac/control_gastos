"""
Constantes globales del proyecto.
Choices reutilizables para todos los modelos.
"""

from django.db import models


class Currency(models.TextChoices):
    """Monedas soportadas por el sistema."""

    ARS = "ARS", "Peso Argentino"
    USD = "USD", "Dólar Estadounidense"


class PaymentMethod(models.TextChoices):
    """Métodos de pago para gastos."""

    CASH = "CASH", "Efectivo"
    DEBIT = "DEBIT", "Tarjeta de Débito"
    CREDIT = "CREDIT", "Tarjeta de Crédito"
    TRANSFER = "TRANSFER", "Transferencia"


class ExpenseType(models.TextChoices):
    """Tipos de gasto."""

    FIXED = "FIXED", "Fijo"
    VARIABLE = "VARIABLE", "Variable"


class CategoryType(models.TextChoices):
    """Tipos de categoría."""

    EXPENSE = "EXPENSE", "Gasto"
    INCOME = "INCOME", "Ingreso"


# Iconos disponibles para categorías personalizadas
CATEGORY_ICON_CHOICES = [
    ("bi-cart", "Compras"),
    ("bi-car-front", "Transporte"),
    ("bi-house", "Vivienda"),
    ("bi-lightning", "Servicios"),
    ("bi-heart-pulse", "Salud"),
    ("bi-controller", "Entretenimiento"),
    ("bi-book", "Educación"),
    ("bi-bag", "Ropa"),
    ("bi-cup-hot", "Café / Restó"),
    ("bi-basket", "Supermercado"),
    ("bi-egg-fried", "Comida"),
    ("bi-truck", "Logística"),
    ("bi-fuel-pump", "Combustible"),
    ("bi-bus-front", "Colectivo"),
    ("bi-airplane", "Viajes"),
    ("bi-phone", "Tecnología"),
    ("bi-laptop", "Freelance"),
    ("bi-wifi", "Internet"),
    ("bi-tv", "Streaming"),
    ("bi-music-note", "Música"),
    ("bi-film", "Cine"),
    ("bi-bicycle", "Deporte"),
    ("bi-trophy", "Objetivos"),
    ("bi-gift", "Regalos"),
    ("bi-people", "Familia"),
    ("bi-person-heart", "Bienestar"),
    ("bi-briefcase", "Trabajo"),
    ("bi-cash", "Dinero"),
    ("bi-cash-coin", "Cobros"),
    ("bi-wallet2", "Billetera"),
    ("bi-bank", "Banco"),
    ("bi-credit-card", "Tarjeta"),
    ("bi-piggy-bank", "Ahorro"),
    ("bi-graph-up-arrow", "Inversiones"),
    ("bi-shop", "Negocio"),
    ("bi-tools", "Mantenimiento"),
    ("bi-house-gear", "Hogar"),
    ("bi-mortarboard", "Cursos"),
    ("bi-box-seam", "Suscripciones"),
    ("bi-stars", "Ocio"),
    ("bi-tag", "General"),
    ("bi-three-dots", "Otros"),
]


# Paleta de colores para categorías (selector visual)
CATEGORY_COLOR_CHOICES = [
    ("#28a745", "Verde"),
    ("#20c997", "Verde agua"),
    ("#17a2b8", "Celeste"),
    ("#007bff", "Azul"),
    ("#6f42c1", "Violeta"),
    ("#e83e8c", "Rosa"),
    ("#dc3545", "Rojo"),
    ("#fd7e14", "Naranja"),
    ("#ffc107", "Amarillo"),
    ("#6c757d", "Gris"),
]

DEFAULT_CATEGORY_COLOR = "#6c757d"


# Grupos del sistema (primer nivel de jerarquía — sin parent)
SYSTEM_GROUPS = {
    "EXPENSE": [
        {"name": "Alimentación", "icon": "bi-cart", "color": "#28a745"},
        {"name": "Transporte", "icon": "bi-car-front", "color": "#17a2b8"},
        {"name": "Vivienda", "icon": "bi-house", "color": "#6c757d"},
        {"name": "Servicios", "icon": "bi-lightning", "color": "#ffc107"},
        {"name": "Salud", "icon": "bi-heart-pulse", "color": "#dc3545"},
        {"name": "Entretenimiento", "icon": "bi-controller", "color": "#e83e8c"},
        {"name": "Educación", "icon": "bi-book", "color": "#6f42c1"},
        {"name": "Ropa", "icon": "bi-bag", "color": "#fd7e14"},
        {"name": "Otros gastos", "icon": "bi-three-dots", "color": "#6c757d"},
        {"name": "Sin clasificar", "icon": "bi-question-circle", "color": "#adb5bd"},
    ],
    "INCOME": [
        {"name": "Sueldo", "icon": "bi-briefcase", "color": "#28a745"},
        {"name": "Freelance", "icon": "bi-laptop", "color": "#17a2b8"},
        {"name": "Inversiones", "icon": "bi-graph-up-arrow", "color": "#6f42c1"},
        {"name": "Otros ingresos", "icon": "bi-three-dots", "color": "#6c757d"},
        {"name": "Sin clasificar", "icon": "bi-question-circle", "color": "#adb5bd"},
    ],
}

# Retrocompatibilidad: SYSTEM_CATEGORIES apunta a SYSTEM_GROUPS
SYSTEM_CATEGORIES = SYSTEM_GROUPS

# Valores por defecto
DEFAULT_CURRENCY = Currency.ARS
DEFAULT_ALERT_THRESHOLD = 80
DEFAULT_EXCHANGE_RATE = 1.0000
