from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from .models import Coach, Booking, CoachRequest
from scheduler.models import Jadwal
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from collections import defaultdict
from django.conf import settings        
from django.conf.urls.static import static 
from reviews_ratings.models import Reviews
from django.db.models import Avg
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

@login_required
def show_catalog(request):
    if request.user.is_superuser:
        return redirect('my_admin:dashboard_simple') 
    if hasattr(request.user, 'is_coach') and request.user.is_coach:
        return redirect('coach_dashboard')
    
    search_query = request.GET.get('q', '')
    country_filter = request.GET.get('country', '')
    sort_by = request.GET.get('sort', 'name')

    countries_list = Coach.objects.values_list('citizenship', flat=True).distinct().order_by('citizenship')

    coaches = Coach.objects.all()

    if search_query:
        coaches = coaches.filter(name__icontains=search_query)
    if country_filter:
        coaches = coaches.filter(citizenship=country_filter)

    if sort_by == 'rate_asc':
        coaches = coaches.order_by('rate_per_session')
    elif sort_by == 'rate_desc':
        coaches = coaches.order_by('-rate_per_session') 
    else: 
        coaches = coaches.order_by(Lower('name'))

    for coach in coaches :
        stats = Reviews.objects.filter(coach=coach).aggregate(avg_rate=Avg('rate'))
        coach.avg_rate = round(stats['avg_rate'] or 0)
        coach.total_reviews = Reviews.objects.filter(coach=coach).count()
        coach.recent_review = Reviews.objects.filter(coach=coach).order_by('-created_at').first()

    paginator = Paginator(coaches, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'country_filter': country_filter,
        'countries_list': countries_list,
        'sort_by': sort_by,
        'app_name': 'Katalog coach'
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "coaches_book_catalog/coach_list_partial.html", context)
    
    return render(request, "coaches_book_catalog/catalog.html", context)

@login_required
def coach_detail(request, coach_id):
    if request.user.is_superuser:
        return redirect('my_admin:dashboard_simple') 
    if hasattr(request.user, 'is_coach') and request.user.is_coach:
        return redirect('coach_dashboard')
    coach = get_object_or_404(Coach, pk=coach_id)
    available_schedules = Jadwal.objects.filter(coach=coach, is_booked=False).order_by('tanggal', 'jam_mulai')
    grouped_schedules = defaultdict(list)
    for jadwal in available_schedules:
        grouped_schedules[jadwal.tanggal].append(jadwal)
    
    reviews = Reviews.objects.filter(coach=coach).order_by('-created_at')
    stats = reviews.aggregate(avg_rate=Avg('rate'))
    avg_rating = round(stats['avg_rate'] or 0, 1)  
    total_reviews = reviews.count()
        
    context = {
        'coach': coach,
        'grouped_schedules': dict(grouped_schedules),
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
    }

    return render(request, 'coaches_book_catalog/coach_detail.html', context)

@login_required
def book_coach(request, jadwal_id):
    if request.user.is_superuser:
        return redirect('my_admin:dashboard_simple') 
    if hasattr(request.user, 'is_coach') and request.user.is_coach:
        return redirect('coach_dashboard')
    if request.method == 'POST':
        jadwal_to_book = get_object_or_404(Jadwal, pk=jadwal_id, is_booked=False)

        jadwal_to_book.is_booked = True
        jadwal_to_book.save()
        booking_notes = request.POST.get('notes', '')
        Booking.objects.create(
            jadwal=jadwal_to_book,
            customer=request.user,
            notes=booking_notes,
        )

        return redirect('show_catalog')

    return redirect('show_catalog')

@login_required
def customer_dashboard(request):
    if request.user.is_superuser:
        return redirect('my_admin:dashboard_simple') 
    if hasattr(request.user, 'is_coach') and request.user.is_coach:
        return redirect('coach_dashboard')
    now = timezone.now()
    print(f"Current time (with TZ): {now}")
    
    all_bookings = Booking.objects.filter(customer=request.user).select_related( 
        'jadwal__coach' 
    ).order_by('jadwal__tanggal', 'jadwal__jam_mulai')

    upcoming_bookings = []
    completed_bookings = []

    for booking in all_bookings:
        if booking.jadwal:

                tz = timezone.get_current_timezone()
                schedule_end_datetime = timezone.make_aware(
                    timezone.datetime.combine(booking.jadwal.tanggal, booking.jadwal.jam_selesai),
                    tz
                )

          
                if schedule_end_datetime > now:
                    upcoming_bookings.append(booking)
                else:
                    completed_bookings.append(booking)

 
    for booking in completed_bookings:
        booking.user_review = Reviews.objects.filter(
            booking=booking
        ).first()

    context = {
        'upcoming_bookings': upcoming_bookings,
        'completed_bookings': completed_bookings,
        'coach_request_pending': CoachRequest.objects.filter(user=request.user, approved=False).exists(),
    }
    return render(request, 'coaches_book_catalog/dashboard_customer.html', context)

@login_required
@require_POST
def update_booking_notes(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if booking.customer != request.user:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    now = timezone.now()
    if booking.jadwal:
        schedule_start_datetime = timezone.make_aware(
            timezone.datetime.combine(booking.jadwal.tanggal, booking.jadwal.jam_mulai),
            timezone.get_current_timezone()
        )
        if schedule_start_datetime < now:
             return JsonResponse({'success': False, 'error': 'Tidak bisa mengedit catatan booking yang sudah lewat.'}, status=400)

    new_notes = request.POST.get('notes', '')
    booking.notes = new_notes
    booking.save()
    return JsonResponse({'success': True, 'message': 'Catatan berhasil diperbarui.'})


@login_required
@require_POST
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user) 

    now = timezone.now()
    if booking.jadwal:
        schedule_start_datetime = timezone.make_aware(
            timezone.datetime.combine(booking.jadwal.tanggal, booking.jadwal.jam_mulai),
            timezone.get_current_timezone()
        )
        if schedule_start_datetime < now:
            messages.error(request, "Booking yang sudah lewat tidak bisa dibatalkan.")
            return redirect('customer_dashboard')

    try:
        with transaction.atomic():
            jadwal_related = booking.jadwal
            if jadwal_related:
                jadwal_related.is_booked = False
                jadwal_related.save()
            booking.delete()
            messages.success(request, "Booking berhasil dibatalkan.")
    except Exception as e:
        messages.error(request, f"Gagal membatalkan booking: {e}")

    return redirect('customer_dashboard')


@login_required
def api_coach_list(request):
    """Return JSON list of coaches. Supports query params: search, citizenship, ordering"""
    search = request.GET.get('search', '')
    citizenship = request.GET.get('citizenship', '')
    ordering = request.GET.get('ordering', '')

    qs = Coach.objects.all()
    if search:
        qs = qs.filter(name__icontains=search)
    if citizenship:
        qs = qs.filter(citizenship=citizenship)

    if ordering:
        if ordering in ['rate', '-rate']:
            # map 'rate' to rate_per_session
            if ordering.startswith('-'):
                qs = qs.order_by('-rate_per_session')
            else:
                qs = qs.order_by('rate_per_session')
        else:
            qs = qs.order_by('name')
    else:
        qs = qs.order_by('name')

    data = []
    for coach in qs:
        foto_url = None
        try:
            if coach.foto and hasattr(coach.foto, 'url'):
                foto_url = request.build_absolute_uri(coach.foto.url)
        except Exception:
            foto_url = None
        # compute avg rate and total reviews
        stats = Reviews.objects.filter(coach=coach).aggregate(avg_rate=Avg('rate'))
        avg_rate = float(stats['avg_rate'] or 0.0)
        total_reviews = Reviews.objects.filter(coach=coach).count()

        data.append({
            'id': coach.id,
            'name': coach.name,
            'age': coach.age,
            'citizenship': coach.citizenship,
            'foto': foto_url,
            'club': coach.club,
            'license': coach.license,
            'preffered_formation': coach.preffered_formation,
            'average_term_as_coach': coach.average_term_as_coach,
            'description': coach.description,
            'rate_per_session': float(coach.rate_per_session),
            'avg_rate': avg_rate,
            'total_reviews': total_reviews,
        })

    return JsonResponse(data, safe=False)


@login_required
def api_coach_detail(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id)
    foto_url = None
    try:
        if coach.foto and hasattr(coach.foto, 'url'):
            foto_url = request.build_absolute_uri(coach.foto.url)
    except Exception:
        foto_url = None

    data = {
        'id': coach.id,
        'name': coach.name,
        'age': coach.age,
        'citizenship': coach.citizenship,
        'foto': foto_url,
        'club': coach.club,
        'license': coach.license,
        'preffered_formation': coach.preffered_formation,
        'average_term_as_coach': coach.average_term_as_coach,
        'description': coach.description,
        'rate_per_session': float(coach.rate_per_session),
    }

    # add aggregate rating info
    stats = Reviews.objects.filter(coach=coach).aggregate(avg_rate=Avg('rate'))
    data['avg_rate'] = float(stats['avg_rate'] or 0.0)
    data['total_reviews'] = Reviews.objects.filter(coach=coach).count()

    return JsonResponse(data)


# ===== BOOKING API =====

@csrf_exempt
def api_booking_list(request):
    """Get list of user's bookings"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required', 'bookings': []}, status=401)
    
    bookings = Booking.objects.filter(customer=request.user).select_related('jadwal', 'jadwal__coach')
    
    data = []
    for booking in bookings:
        if booking.jadwal:
            data.append({
                'id': booking.id,
                'jadwal_id': booking.jadwal.id,
                'customer_id': booking.customer.id,
                'notes': booking.notes or '',
                'coach_id': booking.jadwal.coach.id,
                'coach_name': booking.jadwal.coach.name,
                'date': booking.jadwal.tanggal.strftime('%Y-%m-%d'),
                'start_time': booking.jadwal.jam_mulai.strftime('%H:%M:%S'),
                'end_time': booking.jadwal.jam_selesai.strftime('%H:%M:%S'),
                'rate': float(booking.jadwal.coach.rate_per_session),
            })
    
    return JsonResponse({'bookings': data})


@csrf_exempt
def api_booking_detail(request, booking_id):
    """Get single booking detail"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    
    data = {
        'id': booking.id,
        'jadwal_id': booking.jadwal.id if booking.jadwal else None,
        'customer_id': booking.customer.id,
        'notes': booking.notes or '',
    }
    
    if booking.jadwal:
        data['coach_name'] = booking.jadwal.coach.name
        data['date'] = booking.jadwal.tanggal.strftime('%Y-%m-%d')
        data['start_time'] = booking.jadwal.jam_mulai.strftime('%H:%M:%S')
        data['end_time'] = booking.jadwal.jam_selesai.strftime('%H:%M:%S')
        data['rate'] = float(booking.jadwal.coach.rate_per_session)
    
    return JsonResponse(data)


@csrf_exempt
@require_POST
def api_booking_create(request):
    """Create new booking"""
    import json
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required', 'success': False}, status=401)
    
    try:
        data = json.loads(request.body)
        jadwal_id = data.get('jadwal_id')
        notes = data.get('notes', '')
        
        if not jadwal_id:
            return JsonResponse({'error': 'jadwal_id is required', 'success': False}, status=400)
        
        # Get the jadwal
        jadwal = get_object_or_404(Jadwal, id=jadwal_id)
        
        # Check if already booked
        if jadwal.is_booked:
            return JsonResponse({'error': 'Jadwal sudah dibooking', 'success': False}, status=400)
        
        # Create booking
        with transaction.atomic():
            booking = Booking.objects.create(
                jadwal=jadwal,
                customer=request.user,
                notes=notes
            )
            jadwal.is_booked = True
            jadwal.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking berhasil dibuat',
            'booking_id': booking.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=500)


@csrf_exempt
@require_POST
def api_booking_update(request, booking_id):
    """Update booking notes"""
    import json
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required', 'success': False}, status=401)
    
    try:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        data = json.loads(request.body)
        
        booking.notes = data.get('notes', booking.notes)
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking berhasil diupdate'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON', 'success': False}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'success': False}, status=500)


@csrf_exempt
@require_POST
def api_booking_delete(request, booking_id):
    """Delete booking"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required', 'success': False}, status=401)
    
    try:
        booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
        
        # Free up the jadwal
        with transaction.atomic():
            if booking.jadwal:
                booking.jadwal.is_booked = False
                booking.jadwal.save()
            booking.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Booking berhasil dihapus'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)