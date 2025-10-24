from django.contrib.auth import get_user_model
from .models import Conversation

User = get_user_model()

def conversations_for_user(user: User):
    return Conversation.objects.filter(participants=user).order_by("-last_message_at", "-updated_at")
