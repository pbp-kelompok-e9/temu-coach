from django.urls import path
from . import views

urlpatterns = [
    path('add-schedule/', views.add_schedule, name='add_schedule'),
    path('success/', views.success_page, name='success_page'),
    path('delete_schedule/<int:id>/', views.delete_schedule, name='delete_schedule'),
    path('coach-dashboard/', views.coach_dashboard, name='coach_dashboard'),
    path('update_coach_profile/', views.update_coach_profile, name='update_coach_profile'),
    path('api/schedule/', views.api_schedule_list, name='api_schedule_list'),
    path('api/coach-profile/', views.api_coach_profile, name='api_coach_profile'),

]
