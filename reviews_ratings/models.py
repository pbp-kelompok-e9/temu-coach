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
    booking = models.OneToOneField('coaches_book_catalog.Booking', on_delete=models.CASCADE, null=True, blank=True)
    rate = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
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
