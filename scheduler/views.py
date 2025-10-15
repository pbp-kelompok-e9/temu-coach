from django.shortcuts import render, redirect
from .forms import TambahkanJadwalForm

def add_schedule(request):
    if request.method == 'POST':
        form = TambahkanJadwalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('success_page')  # nanti kita atur halamannya
    else:
        form = TambahkanJadwalForm()
    
    return render(request, 'add_schedule.html', {'form': form})

def success_page(request):
    return render(request, 'success.html')


