from django.db import models
from django.contrib.auth.models import User
from coaches_book_catalog.models import Coach
from django.core.validators import MinValueValidator, MaxValueValidator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from my_admin.models import Report
from .forms import ReportForm
from coaches_book_catalog.models import Coach
from django.conf import settings
# Create your models here.
class Reviews(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rate = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('coach', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review for {self.coach.name} by {self.user.username}"
    
    def to_dict(self):
        return {
            "coach": self.coach.name,
            "user": self.user.username,
            "rate": self.rate,
            "review": self.review,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

@login_required
def create_report(request, coach_id):
    coach = get_object_or_404(Coach, id=coach_id)

    # Mencegah user melapor dirinya sendiri (kalau suatu saat coach juga user)
    if request.user == coach.user:
        messages.warning(request, "You cannot report yourself.")
        return redirect('reviews_ratings:coach_reviews', coach_id=coach.id)

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.coach = coach
            report.save()
            messages.success(request, f"Report for coach {coach.user.username} has been submitted.")
            return redirect('reviews_ratings:coach_reviews', coach_id=coach.id)
    else:
        form = ReportForm()

    return render(request, 'reviews_ratings/create_report.html', {
        'form': form,
        'coach': coach,
    })
