from django import forms

class CoachRegisterForm(forms.Form):
    # data login (optional password)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    # data coach
    name = forms.CharField(max_length=50, label="Full Name")
    age = forms.IntegerField()
    citizenship = forms.CharField(max_length=50)
    foto = forms.ImageField(required=False)
    club = forms.CharField(max_length=20)
    license = forms.CharField(max_length=50)
    preffered_formation = forms.CharField(max_length=100, help_text="Contoh: 4-3-3 Attacking")
    average_term_as_coach = forms.FloatField(help_text="Dalam tahun, contoh: 3.5")
    description = forms.CharField(widget=forms.Textarea)
    rate_per_session = forms.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data
