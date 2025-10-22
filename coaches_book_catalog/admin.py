from django.contrib import admin
from .models import Booking, Coach, MockJadwal
# Register your models here.
admin.site.register(Coach)
admin.site.register(Booking)
admin.site.register(MockJadwal)