from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Reviews
from coaches_book_catalog.models import Coach
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib import messages
from coaches_book_catalog.models import Coach
from .forms import ReportForm


# Create your views here.
@csrf_exempt
@require_POST
def create_review(request, coach_id):
    rate = request.POST.get('rate')
    review = request.POST.get('review', '')
    
    coach = Coach.objects.get(id=coach_id)
    
    review_obj = Reviews.objects.update_or_create(
        coach = coach,
        user = request.user,
        # user = User.objects.first(),  # Buat testing
        defaults = {
            'rate': rate,
            'review': review,
        }
    )
    return JsonResponse({
        "success": True,
        "review_id": review_obj[0].id,
        })

@csrf_exempt
@require_POST
def update_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    # review = Reviews.objects.get(id=id, user=User.objects.first())  # Buat testing
    review.rate = request.POST.get('rate')
    review.review = request.POST.get('review')
    review.save()
    return JsonResponse({
        "success": True,
        "review_id": review.id,
        })

@csrf_exempt
@require_POST
def delete_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    # review = Reviews.objects.get(id=id, user=User.objects.first()) # BUAT TEST
    review.delete()
    return JsonResponse({"success": True})


def check_review(request, coach_id) :
    try :
        review = Reviews.objects.get(coach_id=coach_id, user=request.user)
        # review = Reviews.objects.get(coach_id=coach_id, user=User.objects.first())  # BUAT TESTING
        return JsonResponse(
            {
                'has_review': True,
                'review': {
                    'id': review.id,
                    'rate': review.rate,
                    'review': review.review,
                }
            }
        )
    except Reviews.DoesNotExist :
        return JsonResponse({'has_review': False})
    
@login_required
def create_report(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user   
            report.coach = coach          
            report.save()
            messages.success(request, f"Report for coach {coach.name} has been submitted.")
    else:
        form = ReportForm()

    return render(request, 'reviews_ratings/create_report.html', {
        'form': form,
        'coach': coach,
    })