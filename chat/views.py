from django.db.models import Q
from .models import Message
from coaches_book_catalog.models import Coach, Booking
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
import json
User = get_user_model()

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