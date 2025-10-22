from django.urls import path
from . import views

urlpatterns = [
    path('add-schedule/', views.add_schedule, name='add_schedule'),
    path('success/', views.success_page, name='success_page'),

]
