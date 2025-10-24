from django.shortcuts import render, redirect, get_object_or_404
from .forms import TambahkanJadwalForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Coach, Jadwal
from datetime import date, time
from django.http import JsonResponse

@login_required
def add_schedule(request):
    coach = Coach.objects.get(user=request.user)

    if request.method == 'POST':
        form = TambahkanJadwalForm(request.POST)
        if form.is_valid():
            jadwal = form.save(commit=False)
            # nanti kalau login, ambil dari user:
            # jadwal.coach = get_object_or_404(Coach, user=request.user)
            jadwal.coach = coach 
            jadwal.save()
            return redirect('coach_dashboard')

            # kirim response ke JS
            # return JsonResponse({
            #     'success': True,
            #     'tanggal': jadwal.tanggal.strftime("%Y-%m-%d"),
            #     'jam_mulai': jadwal.jam_mulai.strftime("%H:%M"),
            #     'jam_selesai': jadwal.jam_selesai.strftime("%H:%M"),
            #     'is_booked': jadwal.is_booked,
            # })
        else:
            form = TambahkanJadwalForm()
            # return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return render(request, 'add_schedule.html', {'form': form})
    # return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def success_page(request):
    return render(request, 'success.html')



@login_required
def coach_dashboard(request):
    coach = get_object_or_404(Coach, user=request.user)
    jadwal_list = Jadwal.objects.filter(coach=coach).order_by('tanggal', 'jam_mulai')
    # coach = {
    #     'name': 'John Doe',
    #     'citizenship': 'Italy',
    #     'age': 36,
    #     'club': 'Barcelona',
    #     'preffered_formation': '4-3-3 Attacking',
    #     'average_term_as_coach': 3.5,
    #     'license': 'IDUB Global',
    #     'description': 'Lorem ipsum dolor sit amet...',
    #     'foto': None,
    # }

    # jadwal_list = [
    #     {'tanggal': date(2025, 10, 23), 'jam_mulai': time(14, 0), 'jam_selesai': time(17, 0), 'is_booked': True},
    #     {'tanggal': date(2025, 10, 24), 'jam_mulai': time(9, 0), 'jam_selesai': time(12, 0), 'is_booked': False},
    # ]
    return render(request, 'coach_dashboard.html', {'coach': coach, 'jadwal_list': jadwal_list})
