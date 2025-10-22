from django.contrib import admin
from .models import Booking, Coach
from scheduler.models import Jadwal
# Register your models here.
admin.site.register(Coach)
admin.site.register(Booking)
admin.site.register(Jadwal)