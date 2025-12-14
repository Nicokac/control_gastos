"""
URLs para la app de categorías.
"""

from django.urls import path
from . import views

app_name = 'categories'

urlpatterns = [
    path('', views.CategoryListView.as_view(), name='list'),
    path('create/', views.CategoryCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='delete'),
]
