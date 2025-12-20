from django.shortcuts import render, redirect, get_object_or_404
from .forms import TambahkanJadwalForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Coach, Jadwal
from datetime import date, time
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Jadwal
from .decorators import api_login_required  


@api_login_required
def api_schedule_list(request):
    coach_id = request.GET.get('coach')
    qs = Jadwal.objects.all()
    if coach_id:
        qs = qs.filter(coach_id=coach_id)

    data = []
    for j in qs.order_by('tanggal', 'jam_mulai'):
        data.append({
            'id': j.id,
            'coach': j.coach_id,
            'tanggal': j.tanggal.strftime('%Y-%m-%d'),
            'jam_mulai': j.jam_mulai.strftime('%H:%M:%S'),
            'jam_selesai': j.jam_selesai.strftime('%H:%M:%S'),
            'is_booked': j.is_booked,
        })

    return JsonResponse(data, safe=False)

@csrf_exempt
@api_login_required
def add_schedule(request):
    """Add schedule - API endpoint"""
    # Cek apakah coach sudah approved
    try:
        coach = Coach.objects.get(user=request.user)
    except Coach.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'not_found',
            'message': 'Akun Anda masih menunggu persetujuan admin'
        }, status=403)

    if request.method == 'POST':
        form = TambahkanJadwalForm(request.POST)
        if form.is_valid():
            jadwal = form.save(commit=False)
            jadwal.coach = coach
            jadwal.save()
            return JsonResponse({
                'id': jadwal.id,
                'tanggal': jadwal.tanggal.strftime("%Y-%m-%d"),
                'jam_mulai': jadwal.jam_mulai.strftime("%H:%M"),
                'jam_selesai': jadwal.jam_selesai.strftime("%H:%M"),
                'is_booked': jadwal.is_booked,
            })

        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

def success_page(request):
    """Public success page"""
    return render(request, 'success.html')


@csrf_exempt
@require_http_methods(["POST"])
def delete_schedule(request, id):
    """Delete schedule - bisa dipanggil dari web atau API"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Unauthorized'
        }, status=401)
    
    Jadwal.objects.filter(id=id).delete()
    return JsonResponse({'status': 'deleted'})


@login_required
def coach_dashboard(request):
    """Web view untuk coach dashboard"""
    if hasattr(request.user, 'is_customer') and request.user.is_customer:
        return redirect('customer_dashboard') 
    if request.user.is_superuser:
        return redirect('my_admin:dashboard_simple')
    
    coach = get_object_or_404(Coach, user=request.user)
    # Filter to only show upcoming jadwal (tanggal >= hari ini)
    today = date.today()
    jadwal_list = Jadwal.objects.filter(
        coach=coach,
        tanggal__gte=today
    ).select_related('booking__customer').order_by('tanggal', 'jam_mulai')

    return render(request, 'coach_dashboard.html', {'coach': coach, 'jadwal_list': jadwal_list})


@csrf_exempt
@api_login_required
def update_coach_profile(request):
    """Update coach profile - API endpoint"""
    if request.method == 'POST':
        try:
            coach = Coach.objects.get(user=request.user)
        except Coach.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Coach profile not found'
            }, status=404)

        coach.name = request.POST.get('name')
        coach.age = int(request.POST.get('age'))
        coach.citizenship = request.POST.get('citizenship')
        coach.club = request.POST.get('club')
        coach.license = request.POST.get('license')
        coach.preffered_formation = request.POST.get('preffered_formation')
        coach.average_term_as_coach = float(request.POST.get('average_term_as_coach'))
        coach.rate_per_session = request.POST.get('rate_per_session')
        coach.description = request.POST.get('description')

        if 'foto' in request.FILES:
            coach.foto = request.FILES['foto']

        coach.save()
        return JsonResponse({'status': 'success'})

    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)


@api_login_required
def api_coach_profile(request):
    """
    API untuk mendapatkan profile coach dan jadwal mereka
    """
    if not request.user.is_coach:
        return JsonResponse({
            'status': 'error',
            'error': 'forbidden',
            'message': 'User bukan coach'
        }, status=403)
    
    try:
        coach = Coach.objects.get(user=request.user)
    except Coach.DoesNotExist:
        if hasattr(request.user, 'coach_request'):
            coach_request = request.user.coach_request
            
            if not coach_request.approved:
                return JsonResponse({
                    'status': 'pending',
                    'message': 'Akun coach Anda masih menunggu persetujuan dari admin',
                    'coach_data': {
                        'name': coach_request.name,
                        'age': coach_request.age,
                        'citizenship': coach_request.citizenship,
                        'club': coach_request.club,
                        'license': coach_request.license,
                    }
                }, status=200)
        
        return JsonResponse({
            'status': 'error',
            'error': 'not_found',
            'message': 'Profile coach tidak ditemukan. Silakan hubungi admin.'
        }, status=404)

    foto_url = coach.foto.url if coach.foto else None

    jadwal_list = Jadwal.objects.filter(coach=coach).select_related('booking__customer').order_by('tanggal', 'jam_mulai')
    
    jadwal_data = []
    for j in jadwal_list:
        booking_data = None
        if j.is_booked and hasattr(j, 'booking') and j.booking:
            booking_data = {
                'customer': {
                    'username': j.booking.customer.username
                },
                'notes': j.booking.notes if j.booking.notes else ''
            }
        
        jadwal_data.append({
            'id': j.id,
            'tanggal': j.tanggal.strftime('%Y-%m-%d'),
            'jam_mulai': j.jam_mulai.strftime('%H:%M'),
            'jam_selesai': j.jam_selesai.strftime('%H:%M'),
            'is_booked': j.is_booked,
            'booking': booking_data
        })
    
    return JsonResponse({
        'status': 'success',
        'coach': {
            'name': coach.name,
            'age': coach.age,
            'citizenship': coach.citizenship,
            'club': coach.club,
            'license': coach.license,
            'preffered_formation': coach.preffered_formation,
            'average_term_as_coach': coach.average_term_as_coach,
            'description': coach.description,
            'rate_per_session': str(coach.rate_per_session),
            'foto': foto_url,
        },
        'jadwal_list': jadwal_data
    })