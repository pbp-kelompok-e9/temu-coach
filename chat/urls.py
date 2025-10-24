from django.urls import path
from . import views

urlpatterns = [
    path("conversations/", views.conversation_list_create, name="chat_conversations"),
    path(
        "messages/<int:conversation_id>/",
        views.message_list_or_create,
        name="chat_messages",
    ),
    path(
        "messages/<int:conversation_id>/read",
        views.message_mark_read,
        name="chat_mark_read",
    ),
    path("message/<int:message_id>/", views.message_delete, name="chat_message_delete"),
    path("users/", views.users_list, name="chat_users"),
]
