from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('coaches/<slug:slug>/', views.coach_detail, name='coach_detail'),
    path('coaches/<slug:slug>/message/', views.message_coach, name='message_coach'),
    path('coaches/<slug:slug>/request-booking/', views.request_booking, name='request_booking'),
]
