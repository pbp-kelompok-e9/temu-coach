from django.urls import path
from .views import coach_detail, show_catalog, book_coach


urlpatterns = [
    path('', show_catalog, name='show_catalog'),
    path('<int:coach_id>/', coach_detail, name='coach_detail'),
    path('book/<int:jadwal_id>/', book_coach, name='book_coach'),

]