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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

# Custom error handlers
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

handler404 = custom_404
handler500 = custom_500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('my_admin/', include('my_admin.urls')),
    path('', include('coaches_book_catalog.urls')),
    path('accounts/', include('accounts.urls')),  # Includes both web views & API
    path('coach/', include('scheduler.urls')),
    path('reviews/', include('reviews_ratings.urls')),
    path('chat/', include('chat.urls')),
    

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
