from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('coach', 'Coach'),
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='customer'
    )
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    @property
    def is_customer(self):
        # Treat users who selected 'coach' but don't yet have a coach profile (pending approval)
        # as customers for the purposes of navigation and dashboard access.
        return self.user_type == 'customer' or (self.user_type == 'coach' and not hasattr(self, 'coach_profile'))

    @property
    def is_coach(self):
        return self.user_type == 'coach' and hasattr(self, 'coach_profile')

    def __str__(self):
        return self.username