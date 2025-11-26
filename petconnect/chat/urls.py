"""Chat URLs."""
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:conversation_id>/', views.conversation, name='conversation'),
    path('start/<int:user_id>/', views.start_conversation, name='start'),
    path('<int:conversation_id>/messages/', views.get_messages, name='get_messages'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
]



