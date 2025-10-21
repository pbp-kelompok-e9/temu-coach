from django.shortcuts import render

def dashboard_home(request):
    return render(request, 'temu_coach/dashboard.html')

def accounts_placeholder(request):
    return render(request, 'temu_coach/placeholder.html', {'title': 'Profile & Accounts'})

def coaches_placeholder(request):
    return render(request, 'temu_coach/placeholder.html', {'title': 'Coaches & Book Catalog'})

def e_money_placeholder(request):
    return render(request, 'temu_coach/placeholder.html', {'title': 'E-Money'})

def reviews_placeholder(request):
    return render(request, 'temu_coach/placeholder.html', {'title': 'Review & Rating'})

def scheduler_placeholder(request):
    return render(request, 'temu_coach/placeholder.html', {'title': 'Scheduler'})
