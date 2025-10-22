from django.shortcuts import render
from django.http import JsonResponse
from .models import Reviews

# Create your views here.
def create_review(request, coach_id):
    if request.method == "POST" :
        Reviews.objects.create(
            coach_id = request.POST['coach_id'],
            user = request.user,
            rate = request.POST['rate'],
            review = request.POST['review']
        )
        return JsonResponse({"success": True})
    
def update_review(request, id) :
    review = Reviews.objects.get(id=id, user=request.user)
    review.rate = request.POST['rate']
    review.review = request.POST['review']
    review.save()
    return JsonResponse({"success": True})

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