from django.urls import path
from . import views

urlpatterns = [
    path('partners/', views.get_chat_partners, name='chat_partners'),
    path('room/get_or_create/<int:partner_id>/', views.get_or_create_room, name='get_or_create_room'),
    path('room/<int:room_id>/messages/', views.room_messages, name='room_messages'),
    path('room/<int:room_id>/send/', views.send_message, name='send_message'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
]
