# chat/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL

class ChatRoom(models.Model):
    # customer is always a 'customer' (or user without coach_profile)
    customer = models.ForeignKey(
        User, related_name='customer_rooms', on_delete=models.CASCADE
    )
    coach = models.ForeignKey(
        User, related_name='coach_rooms', on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'coach')
        ordering = ['-created_at']

    def clean(self):
        # pastikan role benar: customer + coach
        from accounts.models import CustomUser
        if self.customer == self.coach:
            raise ValidationError("Customer and coach must be different users.")
        # allow only when .user_type sesuai
        if getattr(self.customer, 'user_type', None) != 'customer':
            raise ValidationError("customer field must be a customer user.")
        if getattr(self.coach, 'user_type', None) != 'coach':
            raise ValidationError("coach field must be a coach user.")

    def __str__(self):
        return f'Room: {self.customer.username} <> {self.coach.username}'

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def clean(self):
        # pastikan sender adalah salah satu peserta di room
        if self.sender_id not in (self.room.customer_id, self.room.coach_id):
            raise ValidationError("Sender must be a participant of the room.")

    def __str__(self):
        return f'[{self.created_at}] {self.sender}: {self.text[:40]}'
