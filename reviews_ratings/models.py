from django.db import models
from django.contrib.auth.models import User
from coaches_book_catalog.models import Coach
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class Reviews(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
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
