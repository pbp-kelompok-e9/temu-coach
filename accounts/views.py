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
                login(request, user)
                messages.info(request, f"Anda berhasil login sebagai {username}.")
                
                if user.is_superuser:
                    return redirect('my_admin:dashboard_simple')
                
                elif user.is_coach: 
                    return redirect('coach_dashboard') 
                
                elif user.is_customer:
                    return redirect('customer_dashboard')
                
                else: 
                    messages.warning(request, "Akun Coach Anda sedang menunggu persetujuan admin.")
                    logout(request) 
                    return redirect('login') 
            
            else:
                messages.error(request,"Username atau password salah.")
        else:
            messages.error(request,"Username atau password salah.")
    else: 
        if request.user.is_authenticated:
             if user.is_superuser:
                 return redirect('my_admin:dashboard_simple')
             elif user.is_coach:
                 return redirect('coach_dashboard') 
             elif user.is_customer:
                 return redirect('customer_dashboard')
             else: 
                 logout(request)
                 return redirect('login')
        form = AuthenticationForm()
         
    form = AuthenticationForm() 
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Anda berhasil logout.")
    return redirect('login')


@csrf_exempt 
def login_api(request): # login dari flutter
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'status': False,
                    'message': 'Username dan password harus diisi'
                }, status=400)
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return JsonResponse({
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
                        }
                    }, status=200)
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
                        
                        required_fields = ['age', 'experience_years', 'expertise', 
                                         'certifications', 'location', 'rate_per_session']
                        missing = [f for f in required_fields if not coach_data.get(f)]
                        
                        if missing:
                            return JsonResponse({
                                'status': False,
                                'message': f'Field coach wajib diisi: {", ".join(missing)}'
                            }, status=400)
                        
                        CoachRequest.objects.create(
                            user=user,
                            age=coach_data.get('age'),
                            experience_years=coach_data.get('experience_years'),
                            expertise=coach_data.get('expertise'),
                            certifications=coach_data.get('certifications'),
                            location=coach_data.get('location'),
                            rate_per_session=coach_data.get('rate_per_session'),
                            description=coach_data.get('description', ''),
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