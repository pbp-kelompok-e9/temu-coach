from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from .models import Conversation, Message, ParticipantState
from .services import get_or_create_conversation, unread_count_for_user

User = get_user_model()


def _json_user(u: User):
    return {"id": u.id, "username": u.username}


def _json_conversation(c: Conversation, me: User):
    others = c.participants.exclude(id=me.id)
    return {
        "id": c.id,
        "participants": [_json_user(p) for p in c.participants.all()],
        "other_participants": [_json_user(p) for p in others],
        "last_message": c.last_message,
        "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
        "unread_count": unread_count_for_user(c, me),
    }


@login_required
@require_http_methods(["GET", "POST"])
def conversation_list_create(request):
    me = request.user
    if request.method == "GET":
        qs = (
            Conversation.objects.filter(participants=me)
            .annotate(num=Count("participants"))
            .filter(num__gte=1)
            .order_by("-last_message_at", "-updated_at", "-id")
        )
        data = [_json_conversation(c, me) for c in qs]
        return JsonResponse({"conversations": data})


    target_id = request.POST.get("target_user_id")
    if not target_id:
        return HttpResponseBadRequest("target_user_id is required")
    if str(me.id) == str(target_id):
        return HttpResponseBadRequest("cannot start conversation with yourself")
    try:
        target = User.objects.get(id=target_id)
    except User.DoesNotExist:
        return HttpResponseBadRequest("target user not found")

    convo, _created = get_or_create_conversation(me, target)
    return JsonResponse({"conversation": _json_conversation(convo, me)})


@login_required
@require_http_methods(["GET", "POST"])
def message_list_or_create(request, conversation_id: int):
    me = request.user
    convo = get_object_or_404(Conversation, id=conversation_id)
    if not convo.has_participant(me):
        return HttpResponseForbidden("forbidden")

    if request.method == "GET":

        try:
            limit = max(1, min(int(request.GET.get("limit", 20)), 100))
        except ValueError:
            limit = 20
        direction = request.GET.get("dir", "backward")
        cursor = request.GET.get("cursor") 

        qs = Message.objects.filter(conversation=convo, deleted_at__isnull=True)
        if cursor:
            try:
                cursor_dt = timezone.datetime.fromisoformat(cursor)
                if timezone.is_naive(cursor_dt):
                    cursor_dt = timezone.make_aware(cursor_dt, timezone.get_current_timezone())
            except Exception:
                return HttpResponseBadRequest("invalid cursor")
            if direction == "backward":
                qs = qs.filter(created_at__lt=cursor_dt)
            else:
                qs = qs.filter(created_at__gt=cursor_dt)

        qs = qs.order_by("-created_at" if direction == "backward" else "created_at")[:limit]
        items = list(qs)
        if direction == "backward":
            items.reverse() 

        next_cursor = items[0].created_at.isoformat() if items else cursor
        has_next = (
            Message.objects.filter(conversation=convo, deleted_at__isnull=True)
            .filter(created_at__lt=(items[0].created_at if items else timezone.now()))
            .exists()
            if direction == "backward"
            else Message.objects.filter(conversation=convo, deleted_at__isnull=True)
            .filter(created_at__gt=(items[-1].created_at if items else timezone.now()))
            .exists()
        )

        data = [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "body": m.body,
                "created_at": m.created_at.isoformat(),
                "is_read": m.is_read,
            }
            for m in items
        ]
        return JsonResponse({"messages": data, "next_cursor": next_cursor, "has_next": has_next})

    body = (request.POST.get("body") or "").strip()
    if not body:
        return HttpResponseBadRequest("body is required")
    if len(body) > 4000:
        return HttpResponseBadRequest("message too long")

    msg = Message.objects.create(conversation=convo, sender=me, body=body)
    convo.last_message = body[:500]
    convo.last_message_at = msg.created_at
    convo.save(update_fields=["last_message", "last_message_at", "updated_at"])

    ParticipantState.objects.get_or_create(conversation=convo, user=me)
    for u in convo.participants.exclude(id=me.id):
        ParticipantState.objects.get_or_create(conversation=convo, user=u)

    return JsonResponse(
        {
            "message": {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "body": msg.body,
                "created_at": msg.created_at.isoformat(),
                "is_read": msg.is_read,
            }
        },
        status=201,
    )


@login_required
@require_POST
def message_mark_read(request, conversation_id: int):
    me = request.user
    convo = get_object_or_404(Conversation, id=conversation_id)
    if not convo.has_participant(me):
        return HttpResponseForbidden("forbidden")
    state, _ = ParticipantState.objects.get_or_create(conversation=convo, user=me)
    now = timezone.now()
    state.last_read_at = now
    state.save(update_fields=["last_read_at"])
    Message.objects.filter(
        conversation=convo, deleted_at__isnull=True
    ).exclude(sender=me).filter(created_at__lte=now).update(is_read=True)
    return JsonResponse({"ok": True, "last_read_at": now.isoformat()})


@login_required
@require_http_methods(["DELETE"])
def message_delete(request, message_id: int):
    me = request.user
    msg = get_object_or_404(Message, id=message_id)
    if not msg.conversation.has_participant(me):
        return HttpResponseForbidden("forbidden")
    if msg.sender_id != me.id:
        return HttpResponseForbidden("only sender may delete")
    msg.soft_delete()
    return JsonResponse({"ok": True})


@login_required
@require_GET
def users_list(request):
    """
    Calon kontak. Integrasi role: jika user customer -> tampilkan coach; jika coach -> tampilkan customer.
    """
    me = request.user
    qs = User.objects.exclude(id=me.id)
    if hasattr(me, "user_type"):
        if me.user_type == "customer":
            qs = qs.filter(user_type="coach")
        elif me.user_type == "coach":
            qs = qs.filter(user_type="customer")
    data = [{"id": u.id, "username": u.username} for u in qs.order_by("username")[:200]]
    return JsonResponse({"users": data})
