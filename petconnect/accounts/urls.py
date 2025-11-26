"""Account URLs."""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('edit/', views.edit_profile_view, name='edit_profile'),
]

