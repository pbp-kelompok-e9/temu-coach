from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import JsonResponse # <--- Tambah ini

# --- MODIFIKASI HANDLER ---
def custom_404(request, exception):
    # Kalau request mengarah ke API (misal URL mengandung 'reviews', 'auth', dll)
    # Return JSON biar Flutter gak crash
    if request.path.startswith('/reviews/') or request.path.startswith('/coach/'):
        return JsonResponse({
            'success': False, 
            'error': '404 Not Found (Check URL path)', 
            'path': request.path
        }, status=404)
    
    return render(request, '404.html', status=404)

def custom_500(request):
    # Kalau request mengarah ke API
    if request.path.startswith('/reviews/') or request.path.startswith('/coach/'):
        return JsonResponse({
            'success': False, 
            'error': '500 Internal Server Error (Backend Crash)',
            'message': 'Ada error syntax atau logic di backend python'
        }, status=500)

    return render(request, '500.html', status=500)


handler404 = custom_404
handler500 = custom_500

urlpatterns = [
    path('admin/', admin.site.urls),
    path('my_admin/', include('my_admin.urls')),
    path('', include('coaches_book_catalog.urls')),
    path('accounts/', include('accounts.urls')),
    path('coach/', include('scheduler.urls')),
    path('reviews/', include('reviews_ratings.urls')), # Sudah benar
    path('chat/', include('chat.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)