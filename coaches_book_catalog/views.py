from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from .models import Coach, Booking
from scheduler.models import Jadwal
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from collections import defaultdict
# Create your views here.

def show_catalog(request):
    search_query = request.GET.get('q', '')
    country_filter = request.GET.get('country', '')
    sort_by = request.GET.get('sort', 'name')

    countries_list = Coach.objects.values_list('citizenship', flat=True).distinct().order_by('citizenship')

    coaches = Coach.objects.all()

    if search_query:
        coaches = coaches.filter(name__icontains=search_query)
    if country_filter:
        coaches = coaches.filter(citizenship=country_filter)

    if sort_by == 'rate_asc':
        coaches = coaches.order_by('rate_per_session')
    elif sort_by == 'rate_desc':
        coaches = coaches.order_by('-rate_per_session') 
    else: 
        coaches = coaches.order_by(Lower('name'))

    paginator = Paginator(coaches, 12) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'country_filter': country_filter,
        'countries_list': countries_list,
        'sort_by': sort_by,
        'app_name': 'Katalog coach'
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "coaches_book_catalog/coach_list_partial.html", context)
    
    return render(request, "coaches_book_catalog/catalog.html", context)

def coach_detail(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id)
    available_schedules = Jadwal.objects.filter(coach=coach, is_booked=False).order_by('tanggal', 'jam_mulai')
    grouped_schedules = defaultdict(list)
    for jadwal in available_schedules:
        grouped_schedules[jadwal.tanggal].append(jadwal)
        
    context = {
        'coach': coach,
        'grouped_schedules': dict(grouped_schedules),
    }

    return render(request, 'coaches_book_catalog/coach_detail.html', context)

@login_required
def book_coach(request, jadwal_id):
    if request.method == 'POST':
        jadwal_to_book = get_object_or_404(Jadwal, pk=jadwal_id, is_booked=False)

        jadwal_to_book.is_booked = True
        jadwal_to_book.save()

        Booking.objects.create(
            jadwal=jadwal_to_book,
            customer=request.user
        )

        return redirect('show_catalog')

    return redirect('show_catalog')