from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404

from my_admin.models import Report
from .models import Reviews
from coaches_book_catalog.models import Booking, Coach
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

# --- CREATE REVIEW (VALIDASI MANUAL) ---
@csrf_exempt 
def create_review_for_booking(request, booking_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Expecting POST'}, status=400)

    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    try:
        booking = Booking.objects.get(id=booking_id)
        
        # 1. Validasi Pemilik
        if booking.customer != request.user:
            return JsonResponse({'success': False, 'error': 'User mismatch'}, status=403)

        # 2. VALIDASI WAKTU (SUDAH KEMBALI!)
        # Gabungkan tanggal & jam selesai jadwal
        jadwal = booking.jadwal
        dt = datetime.datetime.combine(jadwal.tanggal, jadwal.jam_selesai)
        
        # Pastikan timezone aware biar akurat
        schedule_end = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        
        # Kalau waktu sekarang BELUM melewati waktu selesai -> Error
        if timezone.now() < schedule_end:
             return JsonResponse({
                 'success': False, 
                 'error': 'Sesi coaching belum selesai. Anda baru bisa memberi review setelah sesi berakhir.'
             }, status=400)

        # 3. Validasi Duplicate (Smart Mode: Kirim ID kalau ada)
        existing_review = Reviews.objects.filter(booking=booking).first()
        
        if existing_review:
            # RETURN ID biar Flutter bisa langsung Update (Jalan Tol)
            return JsonResponse({
                'success': False, 
                'error': 'Review already exists',
                'existing_id': existing_review.id 
            }, status=409) 

        # 4. Create Review Baru
        rate = int(request.POST.get('rate'))
        review_text = request.POST.get('review', '')

        review = Reviews.objects.create(
            coach=booking.jadwal.coach,
            user=request.user,
            booking=booking,
            rate=rate,
            review=review_text,
        )

        return JsonResponse({'success': True, 'review_id': review.id, 'message': 'Success created!'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# --- UPDATE REVIEW (UNIVERSAL JSON) ---
# Mengembalikan JSON agar Web Modal & Flutter sama-sama jalan
@csrf_exempt
@require_POST
def update_review(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    try:
        # Gunakan filter().first() juga disini untuk keamanan ekstra
        review = Reviews.objects.filter(id=id, user=request.user).first()
        
        if not review:
             return JsonResponse({'success': False, 'error': 'Review not found'}, status=404)
        
        rate_raw = request.POST.get('rate')
        if rate_raw:
             review.rate = int(rate_raw)
        
        review.review = request.POST.get('review', review.review)
        review.save()

        # RETURN JSON (Web JS akan baca success:true lalu tutup modal)
        return JsonResponse({
            "success": True, 
            "review_id": review.id, 
            "message": "Review updated successfully"
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# --- DELETE REVIEW (UNIVERSAL JSON) ---
@csrf_exempt
@require_POST
def delete_review(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=401)

    try:
        review = Reviews.objects.filter(id=id, user=request.user).first()
        
        if not review:
            return JsonResponse({'success': False, 'error': 'Review not found'}, status=404)

        review.delete()
        return JsonResponse({"success": True, "message": "Review deleted"})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# reviews_ratings/views.py

# Hapus decorator apapun diatasnya biar aman
def check_review_for_booking(request, booking_id):
    # 1. Debugging Awal
    if not request.user.is_authenticated:
         # Kita return JSON biar tau kalo ini masalah login
        return JsonResponse({'has_review': False, 'debug_message': 'User not authenticated'})

    try:
        # Import manual di dalam biar anti 'NameError'
        from coaches_book_catalog.models import Booking
        from .models import Reviews

        # 2. Logic Utama
        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return JsonResponse({'has_review': False, 'error': 'Booking not found'}, status=404)

        if booking.customer != request.user:
            return JsonResponse({'has_review': False, 'error': 'Not allowed'}, status=403)

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

    except Exception as e:
        # 3. INI PENYELAMATNYA!
        # Kalau ada crash python, kita tangkap dan kirim sebagai JSON.
        # Flutter lu bakal bisa baca ini dan kita tau error aslinya apa.
        return JsonResponse({
            'has_review': False, 
            'CRASH_ERROR': str(e),
            'CRASH_TYPE': str(type(e))
        }, status=200)

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

# reviews_ratings/views.py

@require_GET
def get_reviews_by_coach(request, coach_id):
    try:
        # Gunakan try-except manual daripada get_object_or_404 biar bisa return JSON
        try:
            coach = Coach.objects.get(id=coach_id)
        except Coach.DoesNotExist:
             return JsonResponse({'status': 'error', 'message': 'Coach not found'}, status=404)

        # Logic ambil review
        reviews = Reviews.objects.filter(coach=coach).order_by('-created_at')

        data = []
        for review in reviews:
            data.append({
                "id": review.id,
                "coach": review.coach.name, 
                "user": review.user.username,
                "rate": review.rate,
                "review": review.review,
                "created_at": review.created_at.isoformat() if review.created_at else None,
                "updated_at": review.updated_at.isoformat() if review.updated_at else None,
            })

        return JsonResponse({
            "status": "success",
            "coach": coach.name,
            "total_reviews": len(data),
            "reviews": data,
        })

    except Exception as e:
        # Tangkap error lain (misal codingan error) dan jadikan JSON
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt  # 1. PENTING: Biar ga diblokir CSRF Django
def create_report(request, coach_id):
    # 2. Cek Login Manual (Return JSON, bukan Redirect HTML)
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Unauthorized: Silakan login kembali.'}, status=401)

    # 3. Cek Coach Ada/Nggak (Return JSON, bukan 404 HTML)
    try:
        coach = Coach.objects.get(id=coach_id)
    except Coach.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'Coach dengan ID {coach_id} tidak ditemukan.'}, status=404)

    # 4. Handle POST
    if request.method == "POST":
        # Handle form-data standard dari Flutter
        reason = request.POST.get("reason", "").strip()
        
        # Jaga-jaga kalau Flutter kirim JSON body (opsional, tapi bagus ada)
        if not reason:
            import json
            try:
                data = json.loads(request.body)
                reason = data.get("reason", "").strip()
            except:
                pass

        if not reason:
            return JsonResponse({"success": False, "error": "Alasan laporan wajib diisi."})

        # Create Report
        try:
            Report.objects.create(
                reporter=request.user,
                coach=coach,
                reason=reason
            )
            return JsonResponse({"success": True, "message": "Laporan berhasil dikirim."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=405)