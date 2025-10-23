from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify
from .forms import CoachRegisterForm
from coaches_book_catalog.models import CoachRequest

def register(request):
    if request.method == "POST":
        form = CoachRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                name = form.cleaned_data["name"]
                password = form.cleaned_data["password1"]

                # Buat username otomatis dari name
                base_username = slugify(name)
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                # Buat user
                user = User.objects.create_user(username=username, password=password)

                # Buat CoachRequest
                CoachRequest.objects.create(
                    user=user,
                    name=name,
                    age=form.cleaned_data["age"],
                    citizenship=form.cleaned_data["citizenship"],
                    foto=form.cleaned_data.get("foto"),
                    club=form.cleaned_data["club"],
                    license=form.cleaned_data["license"],
                    preffered_formation=form.cleaned_data["preffered_formation"],
                    average_term_as_coach=form.cleaned_data["average_term_as_coach"],
                    description=form.cleaned_data["description"],
                    rate_per_session=form.cleaned_data["rate_per_session"],
                )

                messages.success(
                    request,
                    "Your coach registration has been submitted successfully! Please wait for admin approval."
                )
                return redirect("my_admin:dashboard_simple")
    else:
        form = CoachRegisterForm()
    
    return render(request, "register.html", {"form": form})
