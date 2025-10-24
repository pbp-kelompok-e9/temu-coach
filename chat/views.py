from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import ChatRoom, Message
from accounts.models import CustomUser
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def get_chat_partners(request):
    user = request.user
    q = request.GET.get('q', '').strip().lower()
    data = []

    if user.user_type == "customer":
        coaches = CustomUser.objects.filter(user_type="coach")
        if q:
            coaches = coaches.filter(username__icontains=q)
        for c in coaches:
            data.append({"id": c.id, "username": c.username})
    elif user.user_type == "coach":
        rooms = ChatRoom.objects.filter(coach=user)
        for r in rooms:
            customer = r.customer
            if q and q not in customer.username.lower():
                continue
            data.append({"id": customer.id, "username": customer.username, "room_id": r.id})

    return JsonResponse({"partners": data})

@login_required
def get_or_create_room(request, partner_id):
    user = request.user
    partner = get_object_or_404(CustomUser, pk=partner_id)

    if user.user_type == "customer" and partner.user_type != "coach":
        return HttpResponseForbidden("Customer can only chat with coach")
    if user.user_type == "coach" and partner.user_type != "customer":
        return HttpResponseForbidden("Coach can only chat with customer")

    # cari room
    if user.user_type == "customer":
        room, _ = ChatRoom.objects.get_or_create(customer=user, coach=partner)
    else:
        room, _ = ChatRoom.objects.get_or_create(customer=partner, coach=user)

    return JsonResponse({"room_id": room.id})


@login_required
def room_messages(request, room_id):
    room = get_object_or_404(ChatRoom, pk=room_id)
    user = request.user

    if user.id not in (room.customer_id, room.coach_id):
        return HttpResponseForbidden("You are not a participant of this room.")

    limit = int(request.GET.get('limit', 100))
    messages = room.messages.all().order_by('created_at')[:limit]

    data = []
    for m in messages:
        data.append({
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_username": m.sender.username,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
        })
    return JsonResponse({"messages": data})


@login_required
@require_http_methods(["POST"])
def send_message(request, room_id):
    room = get_object_or_404(ChatRoom, pk=room_id)
    user = request.user

    if user.id not in (room.customer_id, room.coach_id):
        return HttpResponseForbidden("You are not a participant of this room.")

    text = request.POST.get('text') or request.body.decode('utf-8')
    if not text.strip():
        return HttpResponseBadRequest("Empty message.")

    msg = Message.objects.create(room=room, sender=user, text=text.strip())
    return JsonResponse({
        "id": msg.id,
        "sender_id": msg.sender_id,
        "sender_username": msg.sender.username,
        "text": msg.text,
        "created_at": msg.created_at.isoformat(),
    })

@login_required
@require_http_methods(["PUT"])
def edit_message(request, message_id):
    msg = get_object_or_404(Message, pk=message_id)
    if msg.sender != request.user:
        return HttpResponseForbidden("You can only edit your own messages.")
    try:
        data = json.loads(request.body.decode())
        text = data.get("text", "").strip()
    except Exception:
        return HttpResponseBadRequest("Invalid request data.")
    if not text:
        return HttpResponseBadRequest("Message cannot be empty.")
    msg.text = text
    msg.save()
    return JsonResponse({
        "id": msg.id,
        "sender_id": msg.sender.id,
        "sender_username": msg.sender.username,
        "text": msg.text,
        "created_at": msg.created_at.isoformat(),
    })

@login_required
@require_http_methods(["DELETE"])
def delete_message(request, message_id):
    msg = get_object_or_404(Message, pk=message_id)
    if msg.sender != request.user:
        return HttpResponseForbidden("You can only delete your own messages.")
    msg.delete()
    return JsonResponse({"success": True, "id": message_id})