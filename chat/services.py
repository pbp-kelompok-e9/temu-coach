from django.contrib.auth import get_user_model
from django.db.models import Count
from .models import Conversation, ParticipantState

User = get_user_model()


def get_or_create_conversation(a: User, b: User):
    """
    Cari percakapan yang pesertanya persis {a,b}. Jika tidak ada -> buat.
    """
    qs = (
        Conversation.objects.filter(participants=a)
        .filter(participants=b)
        .annotate(num=Count("participants"))
        .filter(num=2)
    )
    convo = qs.first()
    created = False
    if not convo:
        convo = Conversation.objects.create()
        convo.participants.add(a, b)
        ParticipantState.objects.get_or_create(conversation=convo, user=a)
        ParticipantState.objects.get_or_create(conversation=convo, user=b)
        created = True
    return convo, created


def unread_count_for_user(convo: Conversation, me: User) -> int:
    state, _ = ParticipantState.objects.get_or_create(conversation=convo, user=me)
    last = state.last_read_at
    qs = convo.messages.exclude(sender=me).filter(deleted_at__isnull=True)
    if last:
        qs = qs.filter(created_at__gt=last)
    return qs.count()
