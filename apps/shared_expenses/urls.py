"""URLs para gastos compartidos."""

from django.urls import path

from . import views

app_name = "shared_expenses"

urlpatterns = [
    path("", views.SharedExpenseListView.as_view(), name="list"),
    path("export/", views.SharedExpenseExportView.as_view(), name="export"),
    path("create/", views.SharedExpenseCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.SharedExpenseUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.SharedExpenseDeleteView.as_view(), name="delete"),
    path("members/", views.HouseholdMemberListView.as_view(), name="members"),
    path("members/add/", views.HouseholdMemberCreateView.as_view(), name="member_create"),
    path(
        "members/<int:pk>/delete/", views.HouseholdMemberDeleteView.as_view(), name="member_delete"
    ),
]
