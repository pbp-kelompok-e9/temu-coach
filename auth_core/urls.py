from django.urls import path
from . import views

app_name = 'auth_core'

urlpatterns = [
    path('', views.Home, name='auth_index'),
    path('register/', views.RegisterView, name='auth_register'),
    path('login/', views.LoginView, name='auth_login'),
    path('logout/', views.LogoutView, name='auth_logout'),
    path('forgot-password/', views.ForgotPassword, name='auth_forgot_password'),
    path('password-reset-sent/<str:reset_id>/', views.PasswordResetSent, name='auth_password_reset_sent'),
    path('reset-password/<str:reset_id>/', views.ResetPassword, name='auth_reset_password'),
]