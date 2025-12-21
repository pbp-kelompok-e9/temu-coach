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
    
    today = date.today()
    jadwal_list = Jadwal.objects.filter(
        coach=coach,
        tanggal__gte=today
    ).select_related('booking__customer').order_by('tanggal', 'jam_mulai')

    return render(request, 'coach_dashboard.html', {'coach': coach, 'jadwal_list': jadwal_list})


@csrf_exempt  
@api_login_required
def update_coach_profile(request):
    """
    Update coach profile - Support both multipart and base64
    """
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Method not allowed'
        }, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Sesi berakhir. Silakan login lagi.'
        }, status=401)
    
    print(f"📥 Received update request from user: {request.user.username}")
    print(f"📥 Content-Type: {request.content_type}")
    
    try:
        coach = Coach.objects.get(user=request.user)
    except Coach.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Coach profile not found'
        }, status=404)

    try:
        # Update fields
        if 'name' in request.POST and request.POST.get('name').strip():
            coach.name = request.POST.get('name').strip()
        
        if 'age' in request.POST:
            try:
                age = int(request.POST.get('age'))
                if age < 18 or age > 100:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Age must be between 18 and 100'
                    }, status=400)
                coach.age = age
            except (ValueError, TypeError):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Age must be a valid number'
                }, status=400)
        
        if 'citizenship' in request.POST:
            coach.citizenship = request.POST.get('citizenship', '').strip()
        
        if 'club' in request.POST:
            coach.club = request.POST.get('club', '').strip()
        
        if 'license' in request.POST:
            coach.license = request.POST.get('license', '').strip()
        
        if 'preffered_formation' in request.POST:
            coach.preffered_formation = request.POST.get('preffered_formation', '').strip()
        
        if 'average_term_as_coach' in request.POST:
            try:
                term = float(request.POST.get('average_term_as_coach'))
                if term < 0 or term > 50:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Average term must be between 0 and 50 years'
                    }, status=400)
                coach.average_term_as_coach = term
            except (ValueError, TypeError):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Average term must be a valid number'
                }, status=400)
        
        if 'rate_per_session' in request.POST:
            rate = request.POST.get('rate_per_session', '').strip()
            if rate:
                coach.rate_per_session = rate
        
        if 'description' in request.POST:
            coach.description = request.POST.get('description', '').strip()

        # ✅ Handle foto base64
        if 'foto_base64' in request.POST:
            import base64
            from django.core.files.base import ContentFile
            
            base64_data = request.POST.get('foto_base64')
            foto_name = request.POST.get('foto_name', 'profile.jpg')
            
            print(f'📷 Received base64 image: {len(base64_data)} chars')
            
            try:
                # Decode base64
                image_data = base64.b64decode(base64_data)
                
                # Validate size (5MB max)
                if len(image_data) > 5 * 1024 * 1024:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'File size too large. Maximum 5MB allowed.'
                    }, status=400)
                
                # Delete old photo if exists
                if coach.foto:
                    try:
                        import os
                        from django.conf import settings
                        
                        old_foto_path = os.path.join(settings.MEDIA_ROOT, str(coach.foto))
                        
                        if os.path.exists(old_foto_path):
                            os.remove(old_foto_path)
                            print(f"✅ Old photo deleted: {old_foto_path}")
                    except Exception as e:
                        print(f"⚠️ Error deleting old photo: {e}")
                
                # Save new photo
                coach.foto.save(foto_name, ContentFile(image_data), save=False)
                print(f"✅ New photo saved: {foto_name} ({len(image_data)} bytes)")
                
            except Exception as e:
                print(f"❌ Error processing base64 image: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error processing image: {str(e)}'
                }, status=400)
        
        # ✅ Handle foto multipart (fallback)
        elif 'foto' in request.FILES:
            foto_file = request.FILES['foto']
            
            # Validate size
            if foto_file.size > 5 * 1024 * 1024:
                return JsonResponse({
                    'status': 'error',
                    'message': 'File size too large. Maximum 5MB allowed.'
                }, status=400)
            
            # Validate type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if foto_file.content_type not in allowed_types:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid file type. Only JPEG, PNG, GIF, and WebP allowed.'
                }, status=400)
            
            # Delete old photo
            if coach.foto:
                try:
                    import os
                    from django.conf import settings
                    
                    old_foto_path = os.path.join(settings.MEDIA_ROOT, str(coach.foto))
                    
                    if os.path.exists(old_foto_path):
                        os.remove(old_foto_path)
                        print(f"✅ Old photo deleted: {old_foto_path}")
                except Exception as e:
                    print(f"⚠️ Error deleting old photo: {e}")
                    
            coach.foto = foto_file
            print(f"✅ New photo uploaded: {foto_file.name} ({foto_file.size} bytes)")

        coach.save()
        
        foto_url = coach.foto.url if coach.foto else None
        
        return JsonResponse({
            'status': 'success',
            'message': 'Profile updated successfully',
            'foto_url': foto_url,
            'coach': {
                'id': coach.id, 
                'name': coach.name,
                'age': coach.age,
                'citizenship': coach.citizenship,
                'club': coach.club,
                'license': coach.license,
                'preffered_formation': coach.preffered_formation,
                'average_term_as_coach': float(coach.average_term_as_coach) if coach.average_term_as_coach else 0.0,
                'description': coach.description,
                'rate_per_session': str(coach.rate_per_session),
                'foto': foto_url,
            }
        })
        
    except Exception as e:
        print(f"❌ Error updating coach profile: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while updating profile' 
        }, status=500)
    
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
            'id': coach.id,
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