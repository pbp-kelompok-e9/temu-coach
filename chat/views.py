from django.db.models import Q, Max, OuterRef, Subquery
from .models import Message
from coaches_book_catalog.models import Coach, Booking
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
User = get_user_model()


# ==================== API ENDPOINTS ====================

@csrf_exempt
def api_conversations(request):
    """GET /api/chat/conversations/ - List all conversations for current user"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    user = request.user
    
    # Get all users that have exchanged messages with current user
    sent_to = Message.objects.filter(sender=user).values_list('receiver_id', flat=True)
    received_from = Message.objects.filter(receiver=user).values_list('sender_id', flat=True)
    
    conversation_user_ids = set(sent_to).union(set(received_from))
    
    conversations = []
    for partner_id in conversation_user_ids:
        partner = User.objects.filter(id=partner_id).first()
        if not partner:
            continue
            
        # Get last message
        last_message = Message.objects.filter(
            (Q(sender=user) & Q(receiver=partner)) |
            (Q(sender=partner) & Q(receiver=user))
        ).order_by('-timestamp').first()
        
        # Count unread messages
        unread_count = Message.objects.filter(
            sender=partner, receiver=user, is_read=False
        ).count()
        
        # Get partner display name
        partner_name = partner.username
        if hasattr(partner, 'coach_profile') and partner.coach_profile:
            partner_name = partner.coach_profile.name or partner.username
        elif partner.first_name:
            partner_name = f"{partner.first_name} {partner.last_name}".strip()
        
        conversations.append({
            'partner_id': partner.id,
            'partner_name': partner_name,
            'partner_username': partner.username,
            'partner_type': partner.user_type if hasattr(partner, 'user_type') else 'unknown',
            'last_message': last_message.content if last_message else '',
            'last_message_time': last_message.timestamp.isoformat() if last_message else None,
            'unread_count': unread_count,
        })
    
    # Sort by last message time (most recent first)
    conversations.sort(key=lambda x: x['last_message_time'] or '', reverse=True)
    
    return JsonResponse({'conversations': conversations})


@csrf_exempt
def api_chat_messages(request, receiver_id):
    """
    GET /api/chat/<receiver_id>/ - Get messages with a specific user
    POST /api/chat/<receiver_id>/ - Send message to a user
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    receiver = get_object_or_404(User, id=receiver_id)
    sender = request.user
    
    if receiver == sender:
        return JsonResponse({'error': 'Cannot send message to yourself'}, status=400)
    
    if request.method == 'GET':
        # Get all messages between the two users
        message_list = Message.objects.filter(
            (Q(sender=sender) & Q(receiver=receiver)) |
            (Q(sender=receiver) & Q(receiver=sender))
        ).order_by('timestamp')
        
        # Mark messages as read
        message_list.filter(receiver=sender, is_read=False).update(is_read=True)
        
        # Get receiver display name
        receiver_name = receiver.username
        if hasattr(receiver, 'coach_profile') and receiver.coach_profile:
            receiver_name = receiver.coach_profile.name or receiver.username
        elif receiver.first_name:
            receiver_name = f"{receiver.first_name} {receiver.last_name}".strip()
        
        messages_data = [{
            'id': msg.id,
            'sender_id': msg.sender.id,
            'receiver_id': msg.receiver.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read,
            'is_mine': msg.sender.id == sender.id,
            'can_edit': (timezone.now() - msg.timestamp).total_seconds() <= 300 and msg.sender.id == sender.id,
            'can_delete': (timezone.now() - msg.timestamp).total_seconds() <= 300 and msg.sender.id == sender.id,
        } for msg in message_list]
        
        return JsonResponse({
            'messages': messages_data,
            'receiver_id': receiver.id,
            'receiver_name': receiver_name,
            'receiver_username': receiver.username,
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
        except json.JSONDecodeError:
            content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Message content is required'}, status=400)
        
        msg = Message.objects.create(sender=sender, receiver=receiver, content=content)
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': msg.id,
                'sender_id': msg.sender.id,
                'receiver_id': msg.receiver.id,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'is_read': msg.is_read,
                'is_mine': True,
                'can_edit': True,
                'can_delete': True,
            }
        }, status=201)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_edit_message(request, message_id):
    """PUT /api/chat/message/<message_id>/ - Edit a message"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method != 'PUT':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        msg = Message.objects.get(id=message_id, sender=request.user)
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Message not found or you do not have permission'}, status=404)
    
    # Check 5 minute limit
    time_diff = timezone.now() - msg.timestamp
    if time_diff.total_seconds() > 300:
        return JsonResponse({'error': 'Edit time expired (5 minutes limit)'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    if not new_content:
        return JsonResponse({'error': 'Message content is required'}, status=400)
    
    msg.content = new_content
    msg.save()
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
        }
    })


@csrf_exempt
def api_delete_message(request, message_id):
    """DELETE /api/chat/message/<message_id>/ - Delete a message"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        msg = Message.objects.get(id=message_id, sender=request.user)
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Message not found or you do not have permission'}, status=404)
    
    # Check 5 minute limit
    time_diff = timezone.now() - msg.timestamp
    if time_diff.total_seconds() > 300:
        return JsonResponse({'error': 'Delete time expired (5 minutes limit)'}, status=403)
    
    msg.delete()
    
    return JsonResponse({'success': True})


@csrf_exempt
def api_contacts(request):
    """GET /api/chat/contacts/ - Get list of users that can be contacted"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    user = request.user
    
    if user.is_superuser:
        # Admin can contact all coaches
        users_qs = User.objects.filter(user_type='coach', coach_profile__isnull=False)
    elif hasattr(user, 'is_coach') and user.is_coach:
        # Coach can contact customers who have booked with them
        booked_customer_ids = Booking.objects.filter(
            jadwal__coach__user=user
        ).values_list('customer_id', flat=True)
        
        # Also include customers who have messaged them
        messaging_customer_ids = Message.objects.filter(
            receiver=user
        ).values_list('sender_id', flat=True)
        
        all_customer_ids = set(booked_customer_ids).union(set(messaging_customer_ids))
        users_qs = User.objects.filter(id__in=all_customer_ids).exclude(id=user.id)
    elif hasattr(user, 'is_customer') and user.is_customer:
        # Customer can contact all verified coaches
        users_qs = User.objects.filter(user_type='coach', coach_profile__isnull=False)
    else:
        users_qs = User.objects.none()
    
    contacts = []
    for contact_user in users_qs:
        contact_name = contact_user.username
        if hasattr(contact_user, 'coach_profile') and contact_user.coach_profile:
            contact_name = contact_user.coach_profile.name or contact_user.username
        elif contact_user.first_name:
            contact_name = f"{contact_user.first_name} {contact_user.last_name}".strip()
        
        contacts.append({
            'id': contact_user.id,
            'name': contact_name,
            'username': contact_user.username,
            'user_type': contact_user.user_type if hasattr(contact_user, 'user_type') else 'unknown',
        })
    
    return JsonResponse({'contacts': contacts})


# ==================== WEB VIEWS ====================

@login_required
def chat_list_view(request):
    search_query = request.GET.get('q', '')
    
    
    if request.user.is_superuser:
        users_list_qs = User.objects.filter(user_type='coach', coach_profile__isnull=False)
    
    elif hasattr(request.user, 'is_coach') and request.user.is_coach:
        try:
            coach_profile = request.user.coach_profile 
        except Coach.DoesNotExist:
            coach_profile = get_object_or_404(Coach, user=request.user) 
        
        coach_user_obj = request.user
        booked_customer_ids = Booking.objects.filter(
            jadwal__coach__user=coach_user_obj
        ).values_list('customer_id', flat=True)
        
        messaging_customer_ids = Message.objects.filter(
            receiver=coach_user_obj
        ).values_list('sender_id', flat=True)
        
        all_customer_ids = set(booked_customer_ids).union(set(messaging_customer_ids))
        users_list_qs = User.objects.filter(id__in=all_customer_ids).exclude(id=request.user.id)
        
    elif hasattr(request.user, 'is_customer') and request.user.is_customer:
        users_list_qs = User.objects.filter(user_type='coach', coach_profile__isnull=False)
        
    else:
        users_list_qs = User.objects.none() 
        if hasattr(request.user, 'user_type') and request.user.user_type == 'coach':
             messages.warning(request, "Akun Coach Anda belum disetujui, Anda belum bisa chat.")
        else:
             messages.error(request, "Anda tidak memiliki akses ke chat.")

    
    if search_query:
        users_list_qs = users_list_qs.filter(username__icontains=search_query) 

    context = {
        'users_list': users_list_qs,
        'search_query': search_query,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'chat_user_list_partial.html', context) 

    return render(request, 'chat_list.html', context)

@login_required
def chat_room_view(request, receiver_id):
    receiver = get_object_or_404(User, id=receiver_id)
    sender = request.user

    if receiver == sender:
        messages.error(request, "Anda tidak bisa mengirim pesan ke diri sendiri.")
        return redirect('chat_list')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        
        if request.method == 'PUT':
            try:
                data = json.loads(request.body)
                message_id = data.get('message_id')
                new_content = data.get('content')
                
                msg = Message.objects.get(id=message_id, sender=sender)
                
                time_diff = timezone.now() - msg.timestamp
                if time_diff.total_seconds() > 300: 
                    return JsonResponse({'success': False, 'error': 'Waktu edit sudah habis (5 menit).'}, status=403)

                msg.content = new_content
                msg.save()
                return JsonResponse({'success': True, 'content': msg.content})
            except Message.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Pesan tidak ditemukan atau Anda tidak punya izin.'}, status=404)
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        if request.method == 'DELETE':
            try:
                data = json.loads(request.body)
                message_id = data.get('message_id')
                
                msg = Message.objects.get(id=message_id, sender=sender)

                time_diff = timezone.now() - msg.timestamp
                if time_diff.total_seconds() > 300: 
                    return JsonResponse({'success': False, 'error': 'Waktu hapus sudah habis (5 menit).'}, status=403)
                
                msg.delete()
                return JsonResponse({'success': True})
            except Message.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Pesan tidak ditemukan atau Anda tidak punya izin.'}, status=404)
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        if request.method == 'POST':
            content = request.POST.get('content')
            if content:
                msg = Message.objects.create(sender=sender, receiver=receiver, content=content)
                return JsonResponse({
                    'success': True,
                    'message_id': msg.id,
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime('%H:%M')
                })
            return JsonResponse({'success': False, 'error': 'Pesan tidak boleh kosong.'}, status=400)
    
    if request.method == 'GET':
        message_list = Message.objects.filter(
            (Q(sender=sender) & Q(receiver=receiver)) |
            (Q(sender=receiver) & Q(receiver=sender))
        ).order_by('timestamp')

        message_list.filter(receiver=sender, is_read=False).update(is_read=True)

        context = {
            'receiver_user': receiver,
            'message_list': message_list,
        }
        return render(request, 'chat_room.html', context)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed.'}, status=405)