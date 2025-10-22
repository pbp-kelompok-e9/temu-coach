from django import forms
from .models import Jadwal

class TambahkanJadwalForm(forms.ModelForm):
    class Meta:
        model = Jadwal
        fields = ['tanggal', 'jam_mulai', 'jam_selesai']
        widgets = {
            'tanggal': forms.DateInput(
                attrs={
                    'type': 'date',  
                    'class': 'form-control'
                }
            ),
            'jam_mulai': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),
            'jam_selesai': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'form-control'
                }
            ),
        }
