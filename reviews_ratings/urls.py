from django.urls import path
from .views import create_review

urlpatterns = [
    path('<int:coach_id>/review/', create_review, name='submit_review'),
]