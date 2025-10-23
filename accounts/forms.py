from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from coaches_book_catalog.models import CoachRequest 
from django.core.exceptions import ValidationError

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(
        choices=CustomUser.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="Daftar sebagai:",
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type') 

class CoachRequestForm(forms.ModelForm):
    class Meta:
        model = CoachRequest
        exclude = ['user', 'approved', 'created_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age < 18:
            raise ValidationError("Coach harus berusia minimal 18 tahun.")
        return age