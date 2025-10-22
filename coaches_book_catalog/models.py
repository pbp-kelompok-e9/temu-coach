from django.db import models
from scheduler.models import Jadwal
from django.conf import settings
# Create your models here.
class Coach(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)

    name = models.CharField(max_length=50)
    age = models.PositiveIntegerField()
    citizenship = models.CharField(max_length=50)

    club = models.CharField(max_length=20)
    license = models.CharField(max_length=50)
    preffered_formation = models.CharField(max_length=100, help_text="Contoh: 4-3-3 Attacking")
    average_term_as_coach = models.FloatField(help_text="Dalam tahun, contoh: 3.5")

    description = models.TextField(help_text="Bisa diisi dengan klub terakhir, gaya melatih, dll.")

    rate_per_session = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    

    
class Booking(models.Model):
    jadwal = models.OneToOneField(Jadwal, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)



    