"""Pet URLs."""
from django.urls import path
from . import views

app_name = 'pets'

urlpatterns = [
    path('add/', views.add_pet, name='add'),
    path('<int:pet_id>/', views.pet_profile, name='profile'),
    path('<int:pet_id>/edit/', views.edit_pet, name='edit'),
    path('<int:pet_id>/delete/', views.delete_pet, name='delete'),
    path('<int:pet_id>/follow/', views.follow_pet, name='follow'),
    path('<int:pet_id>/unfollow/', views.unfollow_pet, name='unfollow'),
    path('<int:pet_id>/review/', views.add_review, name='add_review'),
    path('<int:pet_id>/reviews/', views.all_reviews, name='all_reviews'),
]



