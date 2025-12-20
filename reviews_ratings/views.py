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


# New: create review tied to a booking/session. Validates ownership and schedule end time.
@csrf_exempt
@require_POST
@login_required
def create_review_for_booking(request, booking_id):
    try:
        from coaches_book_catalog.models import Booking

        booking = get_object_or_404(Booking, id=booking_id)

        if booking.customer != request.user:
            return JsonResponse({'success': False, 'error': 'Not allowed'}, status=403)

        jadwal = booking.jadwal
        dt = datetime.datetime.combine(jadwal.tanggal, jadwal.jam_selesai)
        schedule_end = timezone.make_aware(dt) if timezone.is_naive(dt) else dt

        if schedule_end > timezone.now():
            return JsonResponse(
                {'success': False, 'error': 'Booking not finished yet'},
                status=400
            )

        if Reviews.objects.filter(booking=booking).exists():
            return JsonResponse(
                {'success': False, 'error': 'Review already exists'},
                status=400
            )

        rate = int(request.POST.get('rate'))
        review_text = request.POST.get('review', '')

        review = Reviews.objects.create(
            coach=booking.jadwal.coach,
            user=request.user,
            booking=booking,
            rate=rate,
            review=review_text,
        )

        return JsonResponse({'success': True, 'review_id': review.id})

    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': str(e)},
            status=500
        )


# function buat handle update review (cuma bisa update kalo user udah pernah review coach tsb)
@csrf_exempt
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
@require_POST
def delete_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    # review = Reviews.objects.get(id=id, user=User.objects.first()) # BUAT TEST
    review.delete()
    return JsonResponse({"success": True})

# function buat ngecek apakah user udah pernah review booking ini
def check_review_for_booking(request, booking_id):
    from coaches_book_catalog.models import Booking
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.customer != request.user:
        return JsonResponse({'success': False, 'error': 'Not allowed'}, status=403)

    try:
        review = Reviews.objects.get(booking=booking)
        return JsonResponse({
            'has_review': True,
            'review': {
                'id': review.id,
                'rate': review.rate,
                'review': review.review,
            }
        })
    except Reviews.DoesNotExist:
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