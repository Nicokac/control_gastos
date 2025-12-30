"""
URLs para la app de presupuestos.
"""

from django.urls import path

from . import views

app_name = "budgets"

urlpatterns = [
    path("", views.BudgetListView.as_view(), name="list"),
    path("create/", views.BudgetCreateView.as_view(), name="create"),
    path("<int:pk>/", views.BudgetDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.BudgetUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.BudgetDeleteView.as_view(), name="delete"),
    path("copy/", views.CopyBudgetsView.as_view(), name="copy"),
]
