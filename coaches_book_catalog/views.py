from django.shortcuts import get_object_or_404, render
from .models import Coach
# Create your views here.

def show_catalog(request):
    all_coaches = Coach.objects.all()

    context = {
        'coaches': all_coaches,
        'app_name': 'Katalog coach'
    }
    return render(request, "coaches_book_catalog/catalog.html", context)

def coach_detail(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id)

    context = {
        'coach': coach
    }

    return render(request, 'coaches_book_catalog/coach_detail.html', context)