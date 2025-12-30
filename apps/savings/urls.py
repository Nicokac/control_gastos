"""
URLs para la app de ahorro.
"""

from django.urls import path

from . import views

app_name = "savings"

urlpatterns = [
    path("", views.SavingListView.as_view(), name="list"),
    path("create/", views.SavingCreateView.as_view(), name="create"),
    path("<int:pk>/", views.SavingDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.SavingUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.SavingDeleteView.as_view(), name="delete"),
    path("<int:pk>/movement/", views.SavingMovementCreateView.as_view(), name="add_movement"),
]
