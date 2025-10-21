from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Prefetch
from django.urls import reverse
from .models import Coach, Package, AvailabilitySlot, Location, Review, MessageInquiry, BookingRequest

def coach_detail(request, slug):
    coach = get_object_or_404(
        Coach.objects.prefetch_related(
            'packages',
            'locations',
            Prefetch('availability', queryset=AvailabilitySlot.objects.all()),
            Prefetch('reviews', queryset=Review.objects.all()),
        ),
        slug=slug
    )
    avg, count = coach.avg_rating
    # Group availability by weekday for simple display
    days = {i: [] for i in range(7)}
    for slot in coach.availability.all():
        days[slot.weekday].append(slot)

    return render(request, 'coaches_book_catalog/coach_detail.html', {
        'coach': coach,
        'avg_rating': round(avg or 0, 1),
        'review_count': count,
        'days': days,
    })

def message_coach(request, slug):
    coach = get_object_or_404(Coach, slug=slug)
    if request.method == 'POST':
        MessageInquiry.objects.create(
            coach=coach,
            name=request.POST.get('name',''),
            email=request.POST.get('email',''),
            message=request.POST.get('message',''),
        )
        return redirect(reverse('catalog:coach_detail', args=[coach.slug]) + '#message-success')
    return redirect('catalog:coach_detail', slug=slug)

def request_booking(request, slug):
    coach = get_object_or_404(Coach, slug=slug)
    if request.method == 'POST':
        pkg_id = request.POST.get('package_id') or None
        BookingRequest.objects.create(
            coach=coach,
            package=Package.objects.filter(id=pkg_id).first() if pkg_id else None,
            name=request.POST.get('name',''),
            email=request.POST.get('email',''),
            requested_date=request.POST.get('requested_date'),
            requested_time=request.POST.get('requested_time'),
            notes=request.POST.get('notes',''),
        )
        return redirect(reverse('catalog:coach_detail', args=[coach.slug]) + '#booking-success')
    return redirect('catalog:coach_detail', slug=slug)
