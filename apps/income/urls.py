from django.urls import path
from . import views

app_name = 'income'

urlpatterns = [
    path('', views.IncomeListView.as_view(), name='list'),
    path('create/', views.IncomeCreateView.as_view(), name='create'),
]