"""URLs para gastos recurrentes."""

from django.urls import path

from . import views

app_name = "recurring"

urlpatterns = [
    path("", views.RecurringExpenseListView.as_view(), name="list"),
    path("create/", views.RecurringExpenseCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.RecurringExpenseUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.RecurringExpenseDeleteView.as_view(), name="delete"),
]
