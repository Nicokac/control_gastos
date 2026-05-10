"""
URLs para la app de ingresos.
"""

from django.urls import path

from . import views

app_name = "income"

urlpatterns = [
    path("", views.IncomeListView.as_view(), name="list"),
    path("export/", views.IncomeExportView.as_view(), name="export"),
    path("create/", views.IncomeCreateView.as_view(), name="create"),
    path("<int:pk>/", views.IncomeDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.IncomeUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.IncomeDeleteView.as_view(), name="delete"),
]
