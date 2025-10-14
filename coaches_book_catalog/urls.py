from django.urls import path
from .views import coach_detail, show_catalog


urlpatterns = [
    path('', show_catalog, name='show_catalog'),
    path('<int:coach_id>/', coach_detail, name='coach_detail'),

]