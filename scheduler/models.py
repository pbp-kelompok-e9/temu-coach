from django.db import models
from coaches_book_catalog.models import Coach

class Jadwal(models.Model):
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name="jadwal")
    tanggal = models.DateField()
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField()
    is_booked = models.BooleanField(default=False)



    def __str__(self):
        return f"{self.coach.name} | {self.tanggal} | {self.jam_mulai} - {self.jam_selesai}"
