from django.urls import path
from . import views

app_name = 'savings'

urlpatterns = [
    path('', views.SavingListView.as_view(), name='list'),
    path('create/', views.SavingCreateView.as_view(), name='create'),
]
