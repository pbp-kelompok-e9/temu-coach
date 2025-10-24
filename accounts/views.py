from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, CoachRequestForm 
from coaches_book_catalog.models import CoachRequest 
from django.contrib import messages
from django.db import transaction 

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