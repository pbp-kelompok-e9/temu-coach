from django.db import models
from django.contrib.auth.models import User
from coaches_book_catalog.models import Coach
import uuid

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report from {self.reporter.username} on {self.coach.user.username}"

class AdminAction(models.Model):
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={"is_active": True})
    report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(
        max_length=20,
        choices=[
            ("APPROVE", "Approve Report"),
            ("REJECT", "Reject Report"),
            ("BAN", "Ban Coach"),
            ("UNBAN", "Unban Coach"),
        ],
    )
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        admin_name = self.admin.username if self.admin else "system"
        return f"{admin_name} {self.action_type} #{self.id}"
    