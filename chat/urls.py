from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/conversations/start/', views.start_conversation, name='start_conversation'),
    path('api/conversations/<str:session_id>/', views.get_conversation, name='get_conversation'),
    path('api/conversations/<str:session_id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('api/chat/', views.send_message, name='send_message'),
    path('api/upload/', views.upload_file, name='upload_file'),
]
