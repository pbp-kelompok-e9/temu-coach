from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Coach, Jadwal
from datetime import date, time

User = get_user_model()

class CoachViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='coach1',
            password='password123',
            user_type='coach'  
        )
        self.coach = Coach.objects.create(
            user=self.user,
            name='John Doe',
            age=35,  
            citizenship='Italy',
            club='AC Milan',  
            license='UEFA B', 
            preffered_formation='4-4-2', 
            average_term_as_coach=2,
            rate_per_session=100,
            description='Test coach' 
        )
        self.client = Client()
        self.client.login(username='coach1', password='password123')

    def test_add_schedule_valid_post(self):
        """Pastikan jadwal baru bisa ditambahkan via POST"""
        url = reverse('add_schedule')
        data = {
            'tanggal': date.today(),
            'jam_mulai': time(10, 0),
            'jam_selesai': time(11, 0),
            'is_booked': False
        }
        response = self.client.post(url, data, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Jadwal.objects.count(), 1)
        jadwal = Jadwal.objects.first()
        self.assertEqual(jadwal.coach, self.coach)

    def test_add_schedule_invalid_form(self):
        """Jika form invalid, tidak membuat jadwal baru"""
        url = reverse('add_schedule')
        data = {  
            'tanggal': '',
            'jam_mulai': '',
            'jam_selesai': ''
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Jadwal.objects.count(), 0)

    def test_coach_dashboard_view(self):
        """Pastikan dashboard coach bisa diakses dan menampilkan data"""
        Jadwal.objects.create(
            coach=self.coach,
            tanggal=date(2025, 10, 24),
            jam_mulai=time(9, 0),
            jam_selesai=time(11, 0),
            is_booked=False
        )
        url = reverse('coach_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coach_dashboard.html')
        self.assertContains(response, 'John Doe')
        self.assertContains(response, '2025-10-24')

    def test_delete_schedule(self):
        """Pastikan jadwal bisa dihapus"""
        jadwal = Jadwal.objects.create(
            coach=self.coach,
            tanggal=date(2025, 10, 24),
            jam_mulai=time(9, 0),
            jam_selesai=time(11, 0),
            is_booked=False
        )
        url = reverse('delete_schedule', args=[jadwal.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Jadwal.objects.count(), 0)

    def test_update_coach_profile(self):
        """Pastikan profil coach bisa diupdate"""
        url = reverse('update_coach_profile')
        data = {
            'name': 'Jane Doe',
            'age': 40,
            'citizenship': 'Spain',
            'club': 'Barcelona',
            'license': 'UEFA A',
            'preffered_formation': '4-3-3',
            'average_term_as_coach': 2.5,
            'rate_per_session': 150,
            'description': 'Experienced coach'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.coach.refresh_from_db()
        self.assertEqual(self.coach.name, 'Jane Doe')
        self.assertEqual(self.coach.club, 'Barcelona')
