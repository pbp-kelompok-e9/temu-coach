from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404

from my_admin.models import Report
from .models import Reviews
from coaches_book_catalog.models import Coach
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import messages
from coaches_book_catalog.models import Coach
from .forms import ReportForm
import datetime
from django.utils import timezone


# Create your views here.

# function buat handle create review (cuma bisa sekali kalo user belum pernah review coach tsb)
@csrf_exempt
@login_required
@require_POST
def create_review(request, coach_id):
    rate = request.POST.get('rate')
    review = request.POST.get('review', '')
    
    coach = Coach.objects.get(id=coach_id)
    
    review_obj = Reviews.objects.update_or_create(
        coach = coach,
        user = request.user,
        # user = User.objects.first(),  # Buat testing
        defaults = {
            'rate': rate,
            'review': review,
        }
    )
    return JsonResponse({
        "success": True,
        "review_id": review_obj[0].id,
        })


# Helper untuk handle login check khusus API (agar tidak redirect ke HTML)
def api_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

@csrf_exempt 
# JANGAN PAKE @login_required DULU (Ini biang kerok redirect HTML)
# JANGAN PAKE @require_POST DULU (Biar kita bisa tau kalau requestnya keganti jadi GET)
def create_review_for_booking(request, booking_id):
    # 1. DEBUG: Cek Method
    if request.method != 'POST':
        return JsonResponse({
            'success': False, 
            'error': f'Wrong method: {request.method}. Expecting POST. Check trailing slash (/) in Flutter URL.'
        }, status=400)

    # 2. DEBUG: Cek Auth Manual
    # Kita cek manual biar ga redirect ke HTML login page
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False, 
            'error': 'User not authenticated. Session cookie might be missing or expired.'
        }, status=401)

    try:
        # Import di dalam biar aman
        from coaches_book_catalog.models import Booking
        from .models import Reviews

        # 3. DEBUG: Cek Booking ID
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Booking ID {booking_id} not found.'}, status=404)

        # 4. Validasi User
        if booking.customer != request.user:
            return JsonResponse({
                'success': False, 
                'error': f'User mismatch. Booking owner: {booking.customer.username}, Request user: {request.user.username}'
            }, status=403)

        # 5. Validasi Waktu (Gw comment dulu biar lolos debug, uncomment kalau JSON udah kebaca)
        # jadwal = booking.jadwal
        # dt = datetime.datetime.combine(jadwal.tanggal, jadwal.jam_selesai)
        # schedule_end = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        # if schedule_end > timezone.now():
        #    return JsonResponse({'success': False, 'error': 'Booking not finished yet'}, status=400)

        # 6. Validasi Duplicate
        if Reviews.objects.filter(booking=booking).exists():
            return JsonResponse({'success': False, 'error': 'Review already exists for this booking.'}, status=400)

        # 7. Ambil Data POST
        rate_raw = request.POST.get('rate')
        review_text = request.POST.get('review', '')

        # Debugging data input
        if not rate_raw:
             return JsonResponse({'success': False, 'error': 'Rate parameter is missing.'}, status=400)

        try:
            rate = int(rate_raw)
        except ValueError:
            return JsonResponse({'success': False, 'error': f'Invalid rate format: {rate_raw}'}, status=400)

        # 8. Create Review
        review = Reviews.objects.create(
            coach=booking.jadwal.coach,
            user=request.user,
            booking=booking,
            rate=rate,
            review=review_text,
        )

        return JsonResponse({'success': True, 'review_id': review.id, 'message': 'Success created!'})

    except Exception as e:
        # INI KUNCINYA: Tangkap semua error server dan kirim sebagai JSON
        # Jadi lo bisa liat error python aslinya di HP lo
        return JsonResponse({
            'success': False, 
            'error': f'SERVER EXCEPTION: {str(e)}',
            'type': str(type(e))
        }, status=500)

# function buat handle update review (cuma bisa update kalo user udah pernah review coach tsb)
@csrf_exempt
@login_required
@require_POST
def update_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    # review = Reviews.objects.get(id=id, user=User.objects.first())  # Buat testing
    review.rate = int(request.POST.get('rate'))
    review.review = request.POST.get('review')
    review.save()
    return JsonResponse({
        "success": True,
        "review_id": review.id,
        })

# function buat handle delete review (cuma bisa delete kalo user udah pernah review coach tsb)
@csrf_exempt
@login_required
@require_POST
def delete_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    # review = Reviews.objects.get(id=id, user=User.objects.first()) # BUAT TEST
    review.delete()
    return JsonResponse({"success": True})

@login_required
# @csrf_exempt # Opsional tergantung setup lo, tapi buat GET biasanya aman
def check_review_for_booking(request, booking_id):
    from coaches_book_catalog.models import Booking
    
    # Gunakan get_object_or_404 atau try-except biasa untuk Booking
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'has_review': False, 'error': 'Booking not found'}, status=404)

    if booking.customer != request.user:
        return JsonResponse({'success': False, 'error': 'Not allowed'}, status=403)

    review = Reviews.objects.filter(booking=booking).first()

    if review:
        return JsonResponse({
            'has_review': True,
            'review': {
                'id': review.id,
                'rate': review.rate,
                'review': review.review,
            }
        })
    else:
        return JsonResponse({'has_review': False})

# keeping old coach-based review check for backward compatibility
def check_review(request, coach_id) :
    try :
        review = Reviews.objects.get(coach_id=coach_id, user=request.user)
        # review = Reviews.objects.get(coach_id=coach_id, user=User.objects.first())  # BUAT TESTING
        return JsonResponse(
            {
                'has_review': True,
                'review': {
                    'id': review.id,
                    'rate': review.rate,
                    'review': review.review,
                }
            }
        )
    except Reviews.DoesNotExist :
        return JsonResponse({'has_review': False})

# function buat ngambil semua review dari coach tertentu
@require_GET
def get_reviews_by_coach(request, coach_id) :

    coach = get_object_or_404(Coach, id=coach_id)
    reviews = Reviews.objects.filter(coach=coach)

    data = []

    for review in reviews : 
        data.append({
            "id": review.id,
            "user": review.user.username,
            "rate": review.rate,
            "review": review.review,
        })

    return JsonResponse({
        "coach": coach.name,
        "coach_id": coach.id,
        "total_reviews": len(data),
        "reviews": data,
    })
    

@login_required
def create_report(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)

    # Handle AJAX / fetch POST request
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        if not reason:
            return JsonResponse({"success": False, "error": "Reason is required."})

        # Buat Report langsung tanpa form
        report = Report.objects.create(
            reporter=request.user,
            coach=coach,
            reason=reason
        )
        messages.success(request, f"Report for coach {coach.name} has been submitted.")
        return JsonResponse({"success": True})

    # Optional: kalau bukan POST (misal buka lewat browser)
    return JsonResponse({"success": False, "error": "Invalid request method."})