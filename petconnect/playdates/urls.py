"""Playdates URLs."""
from django.urls import path
from . import views

app_name = 'playdates'

urlpatterns = [
    path('', views.discover, name='discover'),
    path('suggest/', views.suggest, name='suggest'),
    path('match/', views.smart_match, name='smart_match'),
    path('map/', views.map_view, name='map'),
]

