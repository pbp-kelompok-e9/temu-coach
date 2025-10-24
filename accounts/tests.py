import datetime
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils import timezone
from coaches_book_catalog.models import Coach, CoachRequest, Booking
from scheduler.models import Jadwal
from reviews_ratings.models import Reviews

User = get_user_model()

def create_user(username, password, user_type='customer', is_superuser=False, **extra_fields):
    if is_superuser:
        return User.objects.create_superuser(username=username, password=password, email=f"{username}@example.com", **extra_fields)
    user = User.objects.create_user(username=username, password=password, user_type=user_type, **extra_fields)
    if user_type == 'coach':
        Coach.objects.create(
            user=user, name=username, age=30, citizenship='-', club='-', 
            license='-', preffered_formation='-', average_term_as_coach=0, 
            description='-', rate_per_session=0
        )
    return user

def create_coach_profile(user, name, **extra_fields):
    coach, created = Coach.objects.get_or_create(user=user, defaults={'name': name})
    defaults = {
        'age': 30, 'citizenship': 'Testlandia', 'club': 'Test FC', 'license': 'UEFA Pro',
        'preffered_formation': '4-3-3', 'average_term_as_coach': 5.0,
        'description': 'Deskripsi tes.', 'rate_per_session': Decimal('100000.00')
    }
    defaults.update(extra_fields)
    for key, value in defaults.items():
        setattr(coach, key, value)
    coach.name = name
    coach.save()
    return coach

def get_valid_coach_request_data(username_suffix=''):
    return {
        'name': f'Coach Request {username_suffix}',
        'age': 25,
        'citizenship': 'Testlandia',
        'club': 'Test FC',
        'license': 'UEFA Pro',
        'preffered_formation': '4-4-2',
        'average_term_as_coach': 3.5,
        'description': 'Saya adalah coach hebat.',
        'rate_per_session': Decimal('200000.00'),
    }

class CustomUserMethodTests(TestCase):
    def setUp(self):
        self.customer = create_user('customer_user', 'pw123', user_type='customer')
        self.coach_user = create_user('coach_user', 'pw123', user_type='coach')
        self_approved_coach = create_coach_profile(self.coach_user, 'Approved Coach')
        self.pending_user = User.objects.create_user(username='pending_user', password='pw123', user_type='coach')
        Coach.objects.filter(user=self.pending_user).delete()

    def test_given_user_object_when_converted_to_string_then_returns_username(self):
        username_str = str(self.customer)
        self.assertEqual(username_str, 'customer_user')

    def test_given_customer_user_when_checking_type_then_is_customer_is_true_and_is_coach_is_false(self):
        self.assertTrue(self.customer.is_customer)
        self.assertFalse(self.customer.is_coach)

    def test_given_pending_coach_user_when_checking_type_then_is_customer_is_true_and_is_coach_is_false(self):
        self.assertTrue(self.pending_user.is_customer)
        self.assertFalse(self.pending_user.is_coach)

    def test_given_approved_coach_user_when_checking_type_then_is_customer_is_false_and_is_coach_is_true(self):
        self.assertFalse(self.coach_user.is_customer)
        self.assertTrue(self.coach_user.is_coach)

class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.user_data = {
            'username': 'newcustomer',
            'email': 'customer@test.com',
            'password': 'password123',
            'password2': 'password123',
            'first_name': 'New',
            'last_name': 'Customer',
        }
        self.coach_data = get_valid_coach_request_data('newcoach')

    def test_given_anonymous_user_when_accessing_register_page_get_then_returns_200_and_both_forms(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertTrue('user_form' in response.context)
        self.assertTrue('coach_form' in response.context)

    def test_given_valid_customer_data_when_posting_register_then_creates_customer_logs_in_and_redirects_to_catalog(self):
        data = self.user_data.copy()
        data['user_type'] = 'customer'
        initial_user_count = User.objects.count()
        response = self.client.post(self.register_url, data)
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        new_user = User.objects.get(username='newcustomer')
        self.assertEqual(new_user.user_type, 'customer')
        self.assertRedirects(response, reverse('show_catalog'))
        self.assertEqual(int(self.client.session['_auth_user_id']), new_user.id)

    def test_given_valid_coach_data_when_posting_register_then_creates_pending_user_and_request_and_redirects_to_login(self):
        data = self.user_data.copy()
        data['username'] = 'newcoach'
        data['user_type'] = 'coach'
        data.update(self.coach_data)
        initial_user_count = User.objects.count()
        initial_request_count = CoachRequest.objects.count()
        response = self.client.post(self.register_url, data, follow=True)
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        self.assertEqual(CoachRequest.objects.count(), initial_request_count + 1)
        new_user = User.objects.get(username='newcoach')
        self.assertEqual(new_user.user_type, 'coach')
        self.assertTrue(CoachRequest.objects.filter(user=new_user).exists())
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(response, "Permintaan menjadi coach sedang diproses admin.")

    def test_given_invalid_user_form_when_posting_register_then_returns_200_and_renders_form_with_errors(self):
        data = self.user_data.copy()
        data['user_type'] = 'customer'
        data['username'] = ''
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertFormError(response.context['user_form'], 'username', 'This field is required.')

    def test_given_valid_user_but_invalid_coach_form_when_posting_register_then_returns_200_and_renders_forms_with_errors(self):
        data = self.user_data.copy()
        data['username'] = 'newcoach'
        data['user_type'] = 'coach'
        data.update(self.coach_data)
        data['age'] = 10
        initial_user_count = User.objects.count()
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertFormError(response.context['coach_form'], 'age', 'Coach harus berusia minimal 18 tahun.')
        self.assertContains(response, "Coach form is invalid")
        self.assertEqual(User.objects.count(), initial_user_count)

class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.customer = create_user('customer_user', 'pw123', user_type='customer')
        self.coach_user = create_user('coach_user', 'pw123', user_type='coach')
        self.pending_user = User.objects.create_user(username='pending_user', password='pw123', user_type='coach')
        Coach.objects.filter(user=self.pending_user).delete()
        self.superuser = create_user('super_user', 'pw123', is_superuser=True)

    def test_given_anonymous_user_when_accessing_login_page_get_then_returns_200(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_given_authenticated_customer_when_accessing_login_page_get_then_redirects_to_customer_dashboard(self):
        self.client.login(username='customer_user', password='pw123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('customer_dashboard'))

    def test_given_authenticated_coach_when_accessing_login_page_get_then_redirects_to_coach_dashboard(self):
        self.client.login(username='coach_user', password='pw123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('coach_dashboard'))

    def test_given_authenticated_superuser_when_accessing_login_page_get_then_redirects_to_admin_dashboard(self):
        self.client.login(username='super_user', password='pw123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('my_admin:dashboard_simple'))
        
    def test_given_authenticated_pending_coach_when_accessing_login_page_get_then_logs_out_and_redirects_to_login(self):
        self.client.login(username='pending_user', password='pw123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_given_valid_customer_credentials_when_posting_login_then_logs_in_and_redirects_to_customer_dashboard(self):
        response = self.client.post(self.login_url, {'username': 'customer_user', 'password': 'pw123'})
        self.assertRedirects(response, reverse('customer_dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.customer.id)

    def test_given_valid_coach_credentials_when_posting_login_then_logs_in_and_redirects_to_coach_dashboard(self):
        response = self.client.post(self.login_url, {'username': 'coach_user', 'password': 'pw123'})
        self.assertRedirects(response, reverse('coach_dashboard'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.coach_user.id)

    def test_given_valid_superuser_credentials_when_posting_login_then_logs_in_and_redirects_to_admin_dashboard(self):
        response = self.client.post(self.login_url, {'username': 'super_user', 'password': 'pw123'})
        self.assertRedirects(response, reverse('my_admin:dashboard_simple'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.superuser.id)

    def test_given_pending_coach_credentials_when_posting_login_then_logs_out_and_redirects_to_login_with_warning(self):
        response = self.client.post(self.login_url, {'username': 'pending_user', 'password': 'pw123'})
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any(message.level == messages.WARNING for message in storage))

    def test_given_invalid_credentials_when_posting_login_then_returns_200_and_renders_login_with_error(self):
        response = self.client.post(self.login_url, {'username': 'customer_user', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any(message.level == messages.ERROR for message in storage))

    def test_given_invalid_form_when_posting_login_then_returns_200_and_renders_login_with_error(self):
        response = self.client.post(self.login_url, {'username': '', 'password': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any(message.level == messages.ERROR for message in storage))

class LogoutViewTests(TestCase):
    def test_given_authenticated_user_when_accessing_logout_then_logs_out_and_redirects_to_login(self):
        user = create_user('logout_user', 'password123')
        self.client.login(username='logout_user', password='password123')
        self.assertIn('_auth_user_id', self.client.session)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
