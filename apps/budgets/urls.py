from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.BudgetListView.as_view(), name='list'),
]