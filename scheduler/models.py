from django.db import models

class TambahkanJadwal(models.Model):
    tanggal = models.DateField()
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField()



def __str__(self):
    return f"{self.tanggal} | {self.jam_mulai} - {self.jam_selesai}"
