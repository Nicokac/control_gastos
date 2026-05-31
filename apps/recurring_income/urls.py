"""URLs para ingresos recurrentes."""

from django.urls import path

from . import views

app_name = "recurring_income"

urlpatterns = [
    path("", views.RecurringIncomeListView.as_view(), name="list"),
    path("create/", views.RecurringIncomeCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.RecurringIncomeUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.RecurringIncomeDeleteView.as_view(), name="delete"),
]
