from django import forms
from my_admin.models import Report  # model Report ada di app my_admin

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe your reason for reporting this coach...',
                'class': 'w-full border rounded p-2 focus:ring focus:ring-red-300',
            }),
        }
        labels = {
            'reason': 'Reason for Report',
        }
