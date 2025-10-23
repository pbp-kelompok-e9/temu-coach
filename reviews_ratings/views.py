from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Reviews
from coaches_book_catalog.models import Coach
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

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