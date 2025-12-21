from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, CoachRequestForm 
from coaches_book_catalog.models import CoachRequest 
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json 

User = get_user_model()

def register_view(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        coach_form = None
        if request.POST.get('user_type') == 'coach':
            coach_form = CoachRequestForm(request.POST, request.FILES)
        if user_form.is_valid():
            user_type = user_form.cleaned_data['user_type']
            
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    user.user_type = user_type
                    user.save() 

                    if user_type == 'coach':
                        if coach_form and coach_form.is_valid():
                            coach_request = coach_form.save(commit=False)
                            coach_request.user = user
                            # Auto-generate name from first_name + last_name
                            coach_request.name = f"{user.first_name} {user.last_name}".strip() or user.username
                            coach_request.save()
                            messages.success(request, f'Akun {user.username} dibuat. Permintaan menjadi coach sedang diproses admin.')
                            return redirect('login') 
                        else:
                            raise Exception("Coach form is invalid") 

                    else: 
                        messages.success(request, f'Akun Customer {user.username} berhasil dibuat.')
                        login(request, user) 
                        return redirect('show_catalog') 

            except Exception as e:
                messages.error(request, f'Registrasi gagal. Periksa input Anda. Detail: {e}')
                context = {'user_form': user_form, 'coach_form': coach_form if coach_form else CoachRequestForm()}
                return render(request, 'accounts/register.html', context)
        
        else:
             messages.error(request, 'Registrasi gagal. Periksa input data user Anda.')
             if not coach_form:
                 coach_form = CoachRequestForm()
             context = {'user_form': user_form, 'coach_form': coach_form}
             return render(request, 'accounts/register.html', context)

    else: 
        user_form = UserRegisterForm()
        coach_form = CoachRequestForm()
        
    context = {'user_form': user_form, 'coach_form': coach_form}
    return render(request, 'accounts/register.html', context)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                if hasattr(user, 'coach_request') and not user.coach_request.approved:
                    messages.error(request, "Anda belum di-approve oleh admin sebagai coach.")
                    return redirect('login')

                if user.is_superuser:
                    login(request, user)
                    messages.info(request, f"Anda berhasil login sebagai admin: {username}.")
                    return redirect('my_admin:dashboard_simple')

                if user.is_coach:
                    login(request, user)
                    messages.info(request, f"Anda berhasil login sebagai coach: {username}.")
                    return redirect('coach_dashboard')

                if user.is_customer:
                    login(request, user)
                    messages.info(request, f"Anda berhasil login sebagai customer: {username}.")
                    return redirect('customer_dashboard')

            messages.error(request,"Username atau password salah.")
            return redirect('login')

        else:
            messages.error(request,"Username atau password salah.")
            return redirect('login')

    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('my_admin:dashboard_simple')
        elif request.user.is_coach:
            return redirect('coach_dashboard')
        elif request.user.is_customer:
            return redirect('customer_dashboard')

    return render(request, 'accounts/login.html', {'form': AuthenticationForm()})


def logout_view(request):
    logout(request)
    messages.info(request, "Anda berhasil logout.")
    return redirect('login')


@csrf_exempt 
def login_api(request):
    """Login dari Flutter - dengan explicit cookie setting"""
    if request.method == 'POST':
        try:
            data = None
            raw_body = (request.body or b'').strip()

            if raw_body:
                try:
                    data = json.loads(raw_body)
                except json.JSONDecodeError:
                    data = None

            if isinstance(data, dict):
                username = data.get('username')
                password = data.get('password')
            else:
                username = request.POST.get('username')
                password = request.POST.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'status': False,
                    'message': 'Username dan password harus diisi'
                }, status=400)
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    if hasattr(user, 'coach_request') and not user.coach_request.approved:
                        return JsonResponse({
                            'status': False,
                            'message': 'Anda belum diapprove oleh admin sebagai coach.'
                        }, status=403)
                    
                    # Login user (creates session)
                    login(request, user)
                    
                    # Ensure session is saved
                    request.session.save()
                    
                    # Prepare response data
                    response_data = {
                        'status': True,
                        'message': 'Login berhasil',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'user_type': user.user_type,
                            'is_coach': user.is_coach,
                            'is_customer': user.is_customer,
                            'is_admin': user.is_superuser
                        }
                    }
                    
                    response = JsonResponse(response_data, status=200)
                    
                    # Get session key
                    session_key = request.session.session_key
                    
                    # Set session cookie explicitly
                    response.set_cookie(
                        'sessionid',
                        session_key,
                        max_age=1209600,      # 2 weeks
                        httponly=False,       # Allow JS access for Flutter web
                        secure=True,          # HTTPS only
                        samesite='None',      # Cross-origin support
                        domain=None,          # Let Django handle domain
                    )
                    
                    # Set CSRF cookie explicitly
                    from django.middleware.csrf import get_token
                    csrf_token = get_token(request)
                    
                    response.set_cookie(
                        'csrftoken',
                        csrf_token,
                        max_age=31449600,     # 1 year
                        httponly=False,       # Allow JS access
                        secure=True,          # HTTPS only
                        samesite='None',      # Cross-origin support
                        domain=None,
                    )
                    
                    # Debug logging
                    print('═══════════════════════════════════════')
                    print('🔐 LOGIN API SUCCESS')
                    print('═══════════════════════════════════════')
                    print(f'✓ User: {username}')
                    print(f'✓ Session key: {session_key}')
                    print(f'✓ CSRF token: {csrf_token[:20]}...')
                    print(f'✓ Cookies set in response')
                    print('═══════════════════════════════════════')
                    
                    return response
                else:
                    return JsonResponse({
                        'status': False,
                        'message': 'Akun tidak aktif'
                    }, status=401)
            else:
                return JsonResponse({
                    'status': False,
                    'message': 'Username atau password salah'
                }, status=401)
                
        except Exception as e:
            # Log error with traceback
            print(f'❌ Login API error: {e}')
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'status': False,
                'message': 'Terjadi kesalahan pada server'
            }, status=500)
    
    return JsonResponse({
        'status': False,
        'message': 'Method tidak diizinkan'
    }, status=405)

@csrf_exempt
def register_api(request):
    # register dari flutter
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password1 = data.get('password1')
            password2 = data.get('password2')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            user_type = data.get('user_type', 'customer')
            
            if not username or not password1 or not password2:
                return JsonResponse({
                    'status': False,
                    'message': 'Username dan password harus diisi'
                }, status=400)
            
            if password1 != password2:
                return JsonResponse({
                    'status': False,
                    'message': 'Password tidak cocok'
                }, status=400)
            
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'status': False,
                    'message': 'Username sudah digunakan'
                }, status=400)
            
            if len(password1) < 8:
                return JsonResponse({
                    'status': False,
                    'message': 'Password minimal 8 karakter'
                }, status=400)
            
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        password=password1,
                        first_name=first_name,
                        last_name=last_name
                    )
                    user.user_type = user_type
                    user.save()
                    
                    if user_type == 'coach':
                        coach_data = data.get('coach_data', {})
                        
                        # name can be provided or auto-generated from first_name + last_name
                        required_fields = ['age', 'citizenship', 'club', 'license', 
                                         'preffered_formation', 'average_term_as_coach', 'rate_per_session']
                        missing = [f for f in required_fields if not coach_data.get(f)]
                        
                        if missing:
                            raise Exception(f'Field coach wajib diisi: {", ".join(missing)}')
                        
                        # Use name from coach_data if provided, otherwise auto-generate
                        generated_name = coach_data.get('name', '').strip() or f"{first_name} {last_name}".strip() or username
                        
                        CoachRequest.objects.create(
                            user=user,
                            name=generated_name,
                            age=coach_data.get('age'),
                            citizenship=coach_data.get('citizenship'),
                            foto=None,  # foto bisa diupload nanti
                            club=coach_data.get('club'),
                            license=coach_data.get('license'),
                            preffered_formation=coach_data.get('preffered_formation'),
                            average_term_as_coach=coach_data.get('average_term_as_coach'),
                            description=coach_data.get('description', ''),
                            rate_per_session=coach_data.get('rate_per_session'),
                            approved=False
                        )
                        
                        message = f'Akun coach {username} berhasil dibuat. Menunggu persetujuan admin.'
                    else:
                        message = f'Akun customer {username} berhasil dibuat'
                    
                    return JsonResponse({
                        'status': True,
                        'message': message,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'user_type': user.user_type
                        }
                    }, status=201)
                    
            except Exception as e:
                return JsonResponse({
                    'status': False,
                    'message': f'Gagal membuat akun: {str(e)}'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'status': False,
                'message': 'Format JSON tidak valid'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': False,
                'message': f'Terjadi kesalahan: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': False,
        'message': 'Method tidak diizinkan'
    }, status=405)

@csrf_exempt
def logout_api(request):
    # logout dari flutter
    if request.method == 'POST':
        try:
            username = request.user.username if request.user.is_authenticated else 'Guest'
            logout(request)
            return JsonResponse({
                'status': True,
                'message': f'{username} berhasil logout'
            }, status=200)
        except Exception as e:
            return JsonResponse({
                'status': False,
                'message': f'Terjadi kesalahan: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': False,
        'message': 'Method tidak diizinkan'
    }, status=405) 


def check_session_api(request):
    if request.user.is_authenticated:
        return JsonResponse({
            'is_authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'user_type': request.user.user_type,
                'is_coach': request.user.is_coach,
                'is_customer': request.user.is_customer,
                'is_admin': request.user.is_superuser
            }
        })
    else:
        return JsonResponse({'is_authenticated': False})


def get_current_user_api(request):
    """Get current user info for mobile app session validation"""
    if request.user.is_authenticated:
        return JsonResponse({
            'status': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'user_type': request.user.user_type,
                'is_coach': request.user.is_coach,
                'is_customer': request.user.is_customer,
                'is_admin': request.user.is_superuser
            }
        })
    else:
        return JsonResponse({
            'status': False,
            'message': 'Not authenticated'
        }, status=401)