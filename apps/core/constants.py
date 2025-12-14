"""
Constantes globales del proyecto.
Choices reutilizables para todos los modelos.
"""

from django.db import models


class Currency(models.TextChoices):
    """Monedas soportadas por el sistema."""
    ARS = 'ARS', 'Peso Argentino'
    USD = 'USD', 'Dólar Estadounidense'


class PaymentMethod(models.TextChoices):
    """Métodos de pago para gastos."""
    CASH = 'CASH', 'Efectivo'
    DEBIT = 'DEBIT', 'Tarjeta de Débito'
    CREDIT = 'CREDIT', 'Tarjeta de Crédito'
    TRANSFER = 'TRANSFER', 'Transferencia'


class ExpenseType(models.TextChoices):
    """Tipos de gasto."""
    FIXED = 'FIXED', 'Fijo'
    VARIABLE = 'VARIABLE', 'Variable'


class CategoryType(models.TextChoices):
    """Tipos de categoría."""
    EXPENSE = 'EXPENSE', 'Gasto'
    INCOME = 'INCOME', 'Ingreso'


class BudgetType(models.TextChoices):
    """Tipos de presupuesto."""
    GLOBAL = 'GLOBAL', 'Global Mensual'
    BY_CATEGORY = 'BY_CATEGORY', 'Por Categoría'

# Categorías del sistema (seed data)
SYSTEM_CATEGORIES = {
    'EXPENSE': [
        {'name': 'Alimentación', 'icon': 'bi-cart', 'color': '#28a745'},
        {'name': 'Transporte', 'icon': 'bi-car-front', 'color': '#17a2b8'},
        {'name': 'Vivienda', 'icon': 'bi-house', 'color': '#6c757d'},
        {'name': 'Servicios', 'icon': 'bi-lightning', 'color': '#ffc107'},
        {'name': 'Salud', 'icon': 'bi-heart-pulse', 'color': '#dc3545'},
        {'name': 'Entretenimiento', 'icon': 'bi-controller', 'color': '#e83e8c'},
        {'name': 'Educación', 'icon': 'bi-book', 'color': '#6f42c1'},
        {'name': 'Ropa', 'icon': 'bi-bag', 'color': '#fd7e14'},
        {'name': 'Otros gastos', 'icon': 'bi-three-dots', 'color': '#6c757d'},
    ],
    'INCOME': [
        {'name': 'Sueldo', 'icon': 'bi-briefcase', 'color': '#28a745'},
        {'name': 'Freelance', 'icon': 'bi-laptop', 'color': '#17a2b8'},
        {'name': 'Inversiones', 'icon': 'bi-graph-up-arrow', 'color': '#6f42c1'},
        {'name': 'Otros ingresos', 'icon': 'bi-three-dots', 'color': '#6c757d'},
    ],
}

# Valores por defecto
DEFAULT_CURRENCY = Currency.ARS
DEFAULT_ALERT_THRESHOLD = 80
DEFAULT_EXCHANGE_RATE = 1.0000