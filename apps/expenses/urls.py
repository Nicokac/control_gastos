"""
URLs para la app de gastos.
"""

from django.urls import path

from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.ExpenseListView.as_view(), name="list"),
    path("export/", views.ExpenseExportView.as_view(), name="export"),
    path("import/", views.ExpenseImportView.as_view(), name="import"),
    path("import/confirm/", views.ExpenseImportConfirmView.as_view(), name="import_confirm"),
    path("import/debug/", views.ExpenseImportDebugView.as_view(), name="import_debug"),
    path("create/", views.ExpenseCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ExpenseDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ExpenseUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.ExpenseDeleteView.as_view(), name="delete"),
]
