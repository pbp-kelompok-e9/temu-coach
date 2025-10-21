"""
URL configuration for temu_coach project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path 
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard_home),
    path('dashboard/accounts/', views.accounts_placeholder, name='dashboard_accounts'),
    path('dashboard/coaches/', views.coaches_placeholder, name='dashboard_coaches'),
    path('dashboard/e-money/', views.e_money_placeholder, name='dashboard_e_money'),
    path('dashboard/reviews/', views.reviews_placeholder, name='dashboard_reviews'),
    path('dashboard/scheduler/', views.scheduler_placeholder, name='dashboard_scheduler'),
]
