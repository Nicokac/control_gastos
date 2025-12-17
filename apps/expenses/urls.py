"""URLs para la app de gastos."""


from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.ExpenseListView.as_view(), name='list'),
    path('create/', views.ExpenseCreateView.as_view(), name='create'),
]
