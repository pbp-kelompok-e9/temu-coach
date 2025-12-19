from django.http import JsonResponse
from functools import wraps

def api_login_required(view_func):
    """
    Decorator untuk API endpoint yang memerlukan login.
    Mengembalikan JSON error instead of redirect ke login page.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'error': 'unauthorized',
                'message': 'Anda harus login terlebih dahulu'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper