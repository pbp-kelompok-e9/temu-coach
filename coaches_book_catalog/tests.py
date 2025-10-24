from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
import datetime
from django.contrib import messages

from accounts.models import CustomUser 
from .models import Coach, Booking, CoachRequest
from scheduler.models import Jadwal
from reviews_ratings.models import Reviews

User = CustomUser


def create_user(username, password, user_type='customer', **extra_fields):
    return User.objects.create_user(username=username, password=password, user_type=user_type, **extra_fields)

def create_coach(user, name, **extra_fields):
    defaults = {
        'age': 30,
        'citizenship': 'Testlandia',
        'club': 'Test FC',
        'license': 'UEFA Pro',
        'preffered_formation': '4-3-3',
        'average_term_as_coach': 5.0,
        'description': 'Deskripsi tes.',
        'rate_per_session': Decimal('100000.00')
    }
    defaults.update(extra_fields)
    return Coach.objects.create(user=user, name=name, **defaults)

def create_jadwal(coach, tanggal_offset_days, jam_mulai, jam_selesai, is_booked=False):
    tanggal = timezone.now().date() + datetime.timedelta(days=tanggal_offset_days)
    mulai = datetime.time.fromisoformat(jam_mulai)
    selesai = datetime.time.fromisoformat(jam_selesai)
    return Jadwal.objects.create(
        coach=coach, tanggal=tanggal, jam_mulai=mulai, jam_selesai=selesai, is_booked=is_booked
    )

def create_review(coach, user, rate, review_text="Tes review."):
    return Reviews.objects.create(coach=coach, user=user, rate=rate, review=review_text)


class ShowCatalogViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer_user = create_user('customer1', 'password123', user_type='customer')
        self.coach_user1 = create_user('coachuser1', 'password123', user_type='coach')
        self.coach_user2 = create_user('coachuser2', 'password123', user_type='coach')
        
        self.coach1 = create_coach(
            self.coach_user1, 'Alpha Coach', citizenship='Avalon', rate_per_session=Decimal('150000.00')
        )
        self.coach2 = create_coach(
            self.coach_user2, 'Beta Coach', citizenship='Brimstone', rate_per_session=Decimal('100000.00')
        )
        create_review(self.coach1, self.customer_user, 5) 

    def test_given_no_user_when_accessing_catalog_then_redirects_to_login(self):
        response = self.client.get(reverse('show_catalog'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('show_catalog')}")

    def test_given_customer_logged_in_when_accessing_catalog_then_loads_template_and_shows_coaches(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('show_catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coaches_book_catalog/catalog.html')
        self.assertContains(response, "Alpha Coach")
        self.assertContains(response, "Beta Coach")
        self.assertTrue('page_obj' in response.context)
        self.assertIsNotNone(response.context['page_obj'][0].avg_rate) 

    def test_given_customer_logged_in_when_searching_by_name_then_returns_filtered_results(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('show_catalog'), {'q': 'Alpha'})
        self.assertContains(response, "Alpha Coach")
        self.assertNotContains(response, "Beta Coach")

    def test_given_customer_logged_in_when_filtering_by_country_then_returns_filtered_results(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('show_catalog'), {'country': 'Brimstone'})
        self.assertNotContains(response, "Alpha Coach")
        self.assertContains(response, "Beta Coach")

    def test_given_customer_logged_in_when_sorting_by_rate_asc_then_returns_coaches_in_ascending_price_order(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('show_catalog'), {'sort': 'rate_asc'})
        coaches_in_context = list(response.context['page_obj'])
        self.assertEqual(coaches_in_context[0].name, "Beta Coach")
        self.assertEqual(coaches_in_context[1].name, "Alpha Coach")

    def test_given_customer_logged_in_when_accessing_via_ajax_then_returns_partial_template(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(reverse('show_catalog'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coaches_book_catalog/coach_list_partial.html')


class CoachDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer_user = create_user('cust_detail', 'password123')
        self.coach_user = create_user('coach_detail', 'password123', user_type='coach')
        self.coach = create_coach(self.coach_user, 'Detail Coach')
        self.jadwal = create_jadwal(self.coach, 1, "10:00", "11:00") 
        create_review(self.coach, self.customer_user, 4, "Bagus")

    def test_given_valid_coach_id_when_accessing_detail_then_loads_template_and_shows_data(self):
        response = self.client.get(reverse('coach_detail', args=[self.coach.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coaches_book_catalog/coach_detail.html')
        self.assertContains(response, "Detail Coach")
        self.assertTrue('grouped_schedules' in response.context)
        self.assertEqual(response.context['avg_rating'], 4.0)

    def test_given_invalid_coach_id_when_accessing_detail_then_returns_404(self):
        response = self.client.get(reverse('coach_detail', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_given_coach_with_no_reviews_when_accessing_detail_then_shows_zero_rating(self):
        Reviews.objects.all().delete()
        response = self.client.get(reverse('coach_detail', args=[self.coach.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['reviews'].count(), 0)
        self.assertEqual(response.context['avg_rating'], 0) 


class BookCoachViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer_user = create_user('cust_book', 'password123')
        self.coach_user = create_user('coach_book', 'password123', user_type='coach')
        self.coach = create_coach(self.coach_user, 'Bookable Coach')
        self.jadwal_available = create_jadwal(self.coach, 2, "14:00", "15:00", is_booked=False)
        self.jadwal_booked = create_jadwal(self.coach, 3, "09:00", "10:00", is_booked=True)
        self.book_url_available = reverse('book_coach', args=[self.jadwal_available.id])
        self.book_url_booked = reverse('book_coach', args=[self.jadwal_booked.id])

    def test_given_no_user_when_posting_to_book_then_redirects_to_login(self):
        response = self.client.post(self.book_url_available)
        self.assertRedirects(response, f"{reverse('login')}?next={self.book_url_available}")

    def test_given_user_logged_in_when_getting_book_url_then_redirects_to_catalog(self):
        self.client.login(username='cust_book', password='password123')
        response = self.client.get(self.book_url_available)
        self.assertRedirects(response, reverse('show_catalog')) 

    def test_given_user_and_available_jadwal_when_posting_to_book_then_creates_booking_and_redirects(self):
        self.client.login(username='cust_book', password='password123')
        initial_booking_count = Booking.objects.count()
        response = self.client.post(self.book_url_available, {'notes': 'Test note'})
        self.assertRedirects(response, reverse('show_catalog'))
        self.assertEqual(Booking.objects.count(), initial_booking_count + 1)
        booking = Booking.objects.latest('id')
        self.assertEqual(booking.customer, self.customer_user)
        self.assertEqual(booking.notes, 'Test note')
        self.jadwal_available.refresh_from_db()
        self.assertTrue(self.jadwal_available.is_booked)

    def test_given_user_and_booked_jadwal_when_posting_to_book_then_returns_404(self):
        self.client.login(username='cust_book', password='password123')
        response = self.client.post(self.book_url_booked)
        self.assertEqual(response.status_code, 404)


class CustomerDashboardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer_user = create_user('dash_user', 'password123')
        self.coach_user = create_user('dash_coach', 'password123', user_type='coach')
        self.coach = create_coach(self.coach_user, 'Dashboard Coach')
        
        self.jadwal_upcoming = create_jadwal(self.coach, 2, "10:00", "11:00")
        self.booking_upcoming = Booking.objects.create(jadwal=self.jadwal_upcoming, customer=self.customer_user)
        self.jadwal_completed = create_jadwal(self.coach, -1, "10:00", "11:00") 
        self.booking_completed = Booking.objects.create(jadwal=self.jadwal_completed, customer=self.customer_user)

    def test_given_no_user_when_accessing_dashboard_then_redirects_to_login(self):
        response = self.client.get(reverse('customer_dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('customer_dashboard')}")

    def test_given_user_with_mixed_bookings_when_accessing_dashboard_then_separates_upcoming_and_completed(self):
        self.client.login(username='dash_user', password='password123')
        response = self.client.get(reverse('customer_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.booking_upcoming, response.context['upcoming_bookings'])
        self.assertIn(self.booking_completed, response.context['completed_bookings'])
        self.assertNotIn(self.booking_completed, response.context['upcoming_bookings'])
        self.assertNotIn(self.booking_upcoming, response.context['completed_bookings'])


class UpdateBookingNotesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = create_user('user1_notes', 'password123')
        self.user2 = create_user('user2_notes', 'password123')
        self.coach_user = create_user('coach_notes', 'password123', user_type='coach')
        self.coach = create_coach(self.coach_user, 'Notes Coach')
        
        self.jadwal_upcoming = create_jadwal(self.coach, 2, "10:00", "11:00")
        self.booking_upcoming = Booking.objects.create(jadwal=self.jadwal_upcoming, customer=self.user1, notes="Initial note")
        
        self.jadwal_completed = create_jadwal(self.coach, -1, "10:00", "11:00")
        self.booking_completed = Booking.objects.create(jadwal=self.jadwal_completed, customer=self.user1, notes="Old note")

        self.update_url = reverse('update_booking_notes', args=[self.booking_upcoming.id])
        self.update_url_completed = reverse('update_booking_notes', args=[self.booking_completed.id])

    def test_given_booking_owner_when_updating_notes_on_upcoming_booking_via_ajax_then_returns_json_success_and_updates_notes(self):
        self.client.login(username='user1_notes', password='password123')
        response = self.client.post(
            self.update_url, 
            {'notes': 'Updated note'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.booking_upcoming.refresh_from_db()
        self.assertEqual(self.booking_upcoming.notes, 'Updated note')

    def test_given_non_booking_owner_when_updating_notes_then_returns_403_forbidden(self):
        self.client.login(username='user2_notes', password='password123')
        response = self.client.post(
            self.update_url, 
            {'notes': 'Hacker note'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        self.booking_upcoming.refresh_from_db()
        self.assertEqual(self.booking_upcoming.notes, 'Initial note')

    def test_given_booking_owner_when_updating_notes_on_completed_booking_then_returns_400_bad_request(self):
        self.client.login(username='user1_notes', password='password123')
        response = self.client.post(
            self.update_url_completed, 
            {'notes': 'Late note'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue('error' in response.json())
        self.booking_completed.refresh_from_db()
        self.assertEqual(self.booking_completed.notes, 'Old note')


class CancelBookingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = create_user('user1_cancel', 'password123')
        self.user2 = create_user('user2_cancel', 'password123')
        self.coach_user = create_user('coach_cancel', 'password123', user_type='coach')
        self.coach = create_coach(self.coach_user, 'Cancel Coach')
        
        self.jadwal_upcoming = create_jadwal(self.coach, 2, "10:00", "11:00", is_booked=True)
        self.booking_upcoming = Booking.objects.create(jadwal=self.jadwal_upcoming, customer=self.user1)
        
        self.jadwal_completed = create_jadwal(self.coach, -1, "10:00", "11:00", is_booked=True)
        self.booking_completed = Booking.objects.create(jadwal=self.jadwal_completed, customer=self.user1)

        self.cancel_url = reverse('cancel_booking', args=[self.booking_upcoming.id])
        self.cancel_url_completed = reverse('cancel_booking', args=[self.booking_completed.id])

    def test_given_booking_owner_when_cancelling_upcoming_booking_then_deletes_booking_and_frees_jadwal(self):
        self.client.login(username='user1_cancel', password='password123')
        initial_booking_count = Booking.objects.count()
        response = self.client.post(self.cancel_url)
        self.assertRedirects(response, reverse('customer_dashboard'))
        self.assertEqual(Booking.objects.count(), initial_booking_count - 1)
        self.assertFalse(Booking.objects.filter(pk=self.booking_upcoming.id).exists())
        self.jadwal_upcoming.refresh_from_db()
        self.assertFalse(self.jadwal_upcoming.is_booked)

    def test_given_non_booking_owner_when_cancelling_booking_then_returns_404(self):
        self.client.login(username='user2_cancel', password='password123')
        initial_booking_count = Booking.objects.count()
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Booking.objects.count(), initial_booking_count)
        self.jadwal_upcoming.refresh_from_db()
        self.assertTrue(self.jadwal_upcoming.is_booked) 

    def test_given_booking_owner_when_cancelling_completed_booking_then_redirects_with_error(self):
        self.client.login(username='user1_cancel', password='password123')
        initial_booking_count = Booking.objects.count()
        response = self.client.post(self.cancel_url_completed)
        self.assertRedirects(response, reverse('customer_dashboard'))
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any(message.level == messages.ERROR for message in storage))
        self.assertEqual(Booking.objects.count(), initial_booking_count) 
