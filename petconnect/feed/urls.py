"""Feed URLs."""
from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    path('', views.home, name='home'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('story/create/', views.create_story, name='create_story'),
    path('story/<int:story_id>/', views.view_story, name='view_story'),
]



