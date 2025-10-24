from django.urls import path
from . import views

app_name = 'reviews_ratings'

urlpatterns = [
    path('create/<int:coach_id>/', views.create_review, name='create_review'),
    path('create/booking/<int:booking_id>/', views.create_review_for_booking, name='create_review_booking'),
    path('update/<int:id>/', views.update_review, name='update_review'),
    path('delete/<int:id>/', views.delete_review, name='delete_review'),
    path('check/<int:coach_id>/', views.check_review, name='check_review'),
    path('check/booking/<int:booking_id>/', views.check_review_for_booking, name='check_review_booking'),
    path('report/<int:coach_id>/', views.create_report, name='create_report'),
]