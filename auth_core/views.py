from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.urls import reverse
from .models import *
from django.contrib.auth.forms import AuthenticationForm
User = get_user_model()

@login_required
def Home(request):
    return render(request, 'auth_core/index.html')

def RegisterView(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'customer')

        user_data_has_error = False

        if User.objects.filter(username=username).exists():
            user_data_has_error = True
            messages.error(request, "Username already exists")

        if User.objects.filter(email=email).exists():
            user_data_has_error = True
            messages.error(request, "Email already exists")

        if len(password) < 5:
            user_data_has_error = True
            messages.error(request, "Password must be at least 5 characters")

        if user_data_has_error:
            return redirect('auth_core:auth_register')
        else:
            new_user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
            )
            if hasattr(new_user, 'user_type'):
                new_user.user_type = user_type
                new_user.save()

            if user_type == 'coach':
                pass

            messages.success(request, "Account created. Login now")
            return redirect('auth_core:auth_login')

    return render(request, 'auth_core/register.html')

def LoginView(request):
    if request.method == "POST":
        next_url = request.POST.get('next') or request.GET.get('next')
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.info(request, f"Anda berhasil login sebagai {username}.") 

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            if hasattr(user, 'is_coach') and user.is_coach:
                messages.warning(request, "Coach dashboard belum tersedia.") 
                return redirect('show_catalog')
            else: 
                return redirect('show_catalog')
        
        else: 
            messages.error(request, "Invalid login credentials")

    else: 
        if request.user.is_authenticated:
            if hasattr(request.user, 'is_coach') and request.user.is_coach:
                return redirect('show_catalog') 
            else:
                return redirect('show_catalog') 
        

    form = AuthenticationForm() 
    return render(request, 'auth_core/login.html', {'form': form})

def LogoutView(request):
    logout(request)
    messages.info(request, "Anda berhasil logout.")
    return redirect('auth_core:auth_login')

def ForgotPassword(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            new_password_reset = PasswordReset(user=user)
            new_password_reset.save()
            password_reset_url = reverse('auth_core:auth_reset_password', kwargs={'reset_id': new_password_reset.reset_id})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'
            email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'
            email_message = EmailMessage(
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER,
                [email]
            )
            email_message.send(fail_silently=True)
            return redirect('auth_core:auth_password_reset_sent', reset_id=new_password_reset.reset_id)
        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('auth_core:auth_forgot_password')

    return render(request, 'auth_core/forgot_password.html')

def PasswordResetSent(request, reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'auth_core/password_reset_sent.html')
    else:
        messages.error(request, 'Invalid reset id')
        return redirect('auth_core:auth_forgot_password')

def ResetPassword(request, reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)
        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            passwords_have_error = False
            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, 'Passwords do not match')
            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 5 characters long')
            expiration_time = password_reset_id.created_when + timezone.timedelta(minutes=10)
            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, 'Reset link has expired')
                password_reset_id.delete()

            if not passwords_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()
                password_reset_id.delete()
                messages.success(request, 'Password reset. Proceed to login')
                return redirect('auth_core:auth_login')
            else:
                return redirect('auth_core:auth_reset_password', reset_id=reset_id)

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid reset id')
        return redirect('auth_core:auth_forgot_password')

    return render(request, 'auth_core/reset_password.html')
