from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from .models import Reviews
from coaches_book_catalog.models import Coach

# Create your views here.
@require_POST
def create_review(request, coach_id):
    rate = request.POST.get('rate')
    review = request.POST.get('review', '')
    coach = get_object_or_404(Coach, id=coach_id)
    
    Reviews.objects.update_or_create(
        coach = coach,
        user = request.user,
        defaults = {
            'rate': rate,
            'review': review,
        }
    )
    return JsonResponse({"success": True})

@require_POST
def update_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    review.rate = request.POST.get('rate')
    review.review = request.POST.get('review')
    review.save()
    return JsonResponse({"success": True})

@require_POST
def delete_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    review.delete()
    return JsonResponse({"success": True})


def check_review(request, coach_id) :
    try :
        review = Reviews.objects.get(coach_id=coach_id, user=request.user)
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