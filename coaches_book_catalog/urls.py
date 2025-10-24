from django.urls import path

from accounts import views
from .views import coach_detail, show_catalog, book_coach, customer_dashboard, update_booking_notes, cancel_booking


urlpatterns = [
    path('', show_catalog, name='show_catalog'),
    path('<int:coach_id>/', coach_detail, name='coach_detail'),
    path('book/<int:jadwal_id>/', book_coach, name='book_coach'),
    path('dashboard/', customer_dashboard, name='customer_dashboard'),
    path('booking/<int:booking_id>/update-notes/', update_booking_notes, name='update_booking_notes'),
    path('booking/<int:booking_id>/cancel/', cancel_booking, name='cancel_booking'),
]