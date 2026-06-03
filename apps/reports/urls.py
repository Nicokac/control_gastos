"""
URLs para dashboard y reportes.
"""

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("export/", views.DashboardExportView.as_view(), name="export"),
    path("annual/", views.AnnualReportView.as_view(), name="annual"),
    path("annual/export/", views.AnnualReportExportView.as_view(), name="annual_export"),
]
