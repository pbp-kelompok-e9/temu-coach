from django.urls import path
from . import views

app_name = "my_admin"

urlpatterns = [
    path('', views.dashboard_simple, name='dashboard_simple'),
    path('coach/<int:coach_id>/approve/', views.approve_coach, name='approve_coach'),
    path('coach/<int:coach_id>/reject/', views.reject_coach, name='reject_coach'),
    path('coach/<int:coach_id>/ban/', views.ban_coach, name='ban_coach'),
    path('report/<int:report_id>/delete/', views.delete_report, name='delete_report'),

    path('api/reports/', views.api_reports, name='api_reports'),
    path('api/coach-requests/', views.api_coach_requests, name='api_coach_requests'),
    
    path('api/coach/<int:coach_id>/approve/', views.approve_coach_api, name='approve_coach_api'),
    path('api/coach/<int:coach_id>/reject/', views.reject_coach_api, name='reject_coach_api'),
    path('api/coach/<int:coach_id>/ban/', views.ban_coach_api, name='ban_coach_api'),
    path('api/report/<int:report_id>/delete/', views.delete_report_api, name='delete_report_api'),
    path('reports/create/coach/<int:coach_id>/', views.create_report_api, name='create_report_api'),

]
