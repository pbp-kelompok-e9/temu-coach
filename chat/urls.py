from django.urls import path

from accounts import views
from .views import chat_list_view, chat_room_view


urlpatterns = [
    path('', chat_list_view, name='chat_list'),
    path('<int:receiver_id>/', chat_room_view, name='chat_room'),
]