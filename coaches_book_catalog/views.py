from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from .models import Coach, Booking
from scheduler.models import Jadwal
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from collections import defaultdict
from django.conf import settings        
from django.conf.urls.static import static 
from reviews_ratings.models import Reviews
from django.db.models import Avg
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

    for coach in coaches :
        stats = Reviews.objects.filter(coach=coach).aggregate(avg_rate=Avg('rate'))
        coach.avg_rate = round(stats['avg_rate'] or 0)
        coach.total_reviews = Reviews.objects.filter(coach=coach).count()
        coach.recent_review = Reviews.objects.filter(coach=coach).order_by('-created_at').first()

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
    
    # Get ratings data
    reviews = Reviews.objects.filter(coach=coach).order_by('-created_at')
    stats = reviews.aggregate(avg_rate=Avg('rate'))
    avg_rating = round(stats['avg_rate'] or 0, 1)  # round to 1 decimal place, default to 0 if no ratings
    total_reviews = reviews.count()
        
    context = {
        'coach': coach,
        'grouped_schedules': dict(grouped_schedules),
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': total_reviews,
    }

    return render(request, 'coaches_book_catalog/coach_detail.html', context)

@login_required
def book_coach(request, jadwal_id):
    if request.method == 'POST':
        jadwal_to_book = get_object_or_404(Jadwal, pk=jadwal_id, is_booked=False)

        jadwal_to_book.is_booked = True
        jadwal_to_book.save()
        booking_notes = request.POST.get('notes', '')
        Booking.objects.create(
            jadwal=jadwal_to_book,
            customer=request.user,
            notes=booking_notes,
        )

        return redirect('show_catalog')

    return redirect('show_catalog')