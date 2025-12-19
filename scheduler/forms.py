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
    
    def clean(self):
        cleaned_data = super().clean()
        jam_mulai = cleaned_data.get('jam_mulai')
        jam_selesai = cleaned_data.get('jam_selesai')
        
        if jam_mulai and jam_selesai:
            if jam_selesai <= jam_mulai:
                raise forms.ValidationError(
                    'Jam selesai harus lebih besar dari jam mulai.'
                )
        
        return cleaned_data
