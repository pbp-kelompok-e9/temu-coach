from django.urls import path

from accounts import views
from .views import (
    chat_list_view, 
    chat_room_view,
    api_conversations,
    api_chat_messages,
    api_edit_message,
    api_delete_message,
    api_contacts,
)


urlpatterns = [
    # API endpoints
    path('api/conversations/', api_conversations, name='api_conversations'),
    path('api/contacts/', api_contacts, name='api_contacts'),
    path('api/<int:receiver_id>/', api_chat_messages, name='api_chat_messages'),
    path('api/message/<int:message_id>/edit/', api_edit_message, name='api_edit_message'),
    path('api/message/<int:message_id>/delete/', api_delete_message, name='api_delete_message'),
    
    # Web views
    path('', chat_list_view, name='chat_list'),
    path('<int:receiver_id>/', chat_room_view, name='chat_room'),
]