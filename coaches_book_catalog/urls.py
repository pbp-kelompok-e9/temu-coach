from django.urls import path

from accounts import views
from .views import (
    coach_detail,
    show_catalog,
    book_coach,
    customer_dashboard,
    update_booking_notes,
    cancel_booking,
    api_coach_list,
    api_coach_detail,
    api_booking_list,
    api_booking_detail,
    api_booking_create,
    api_booking_update,
    api_booking_delete,
)


urlpatterns = [
    path('', show_catalog, name='show_catalog'),
    path('<int:coach_id>/', coach_detail, name='coach_detail'),
    path('book/<int:jadwal_id>/', book_coach, name='book_coach'),
    path('dashboard/', customer_dashboard, name='customer_dashboard'),
    path('booking/<int:booking_id>/update-notes/', update_booking_notes, name='update_booking_notes'),
    path('booking/<int:booking_id>/cancel/', cancel_booking, name='cancel_booking'),

    # API endpoints
    path('api/coach/', api_coach_list, name='api_coach_list'),
    path('api/coach/<int:coach_id>/', api_coach_detail, name='api_coach_detail'),
    
    # Booking API endpoints
    path('api/booking/', api_booking_list, name='api_booking_list'),
    path('api/booking/create/', api_booking_create, name='api_booking_create'),
    path('api/booking/<int:booking_id>/', api_booking_detail, name='api_booking_detail'),
    path('api/booking/<int:booking_id>/update/', api_booking_update, name='api_booking_update'),
    path('api/booking/<int:booking_id>/delete/', api_booking_delete, name='api_booking_delete'),
]