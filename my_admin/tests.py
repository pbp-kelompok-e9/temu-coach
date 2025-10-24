from django.test import TestCase, Client
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from accounts.models import CustomUser
from coaches_book_catalog.models import Coach, CoachRequest
from my_admin.models import Report, AdminAction

User = CustomUser


def create_user(username, password, user_type='customer', **extra_fields):
    return User.objects.create_user(username=username, password=password, user_type=user_type, **extra_fields)

def create_coach_request(user, **extra_fields):
    defaults = {
        'name': 'Test Coach',
        'age': 30,
        'citizenship': 'Indonesia',
        'club': 'Test Club',
        'license': 'A',
        'preffered_formation': '4-3-3',
        'average_term_as_coach': 3.0,
        'description': 'Coach test description',
        'rate_per_session': Decimal('100000.00')
    }
    defaults.update(extra_fields)
    return CoachRequest.objects.create(user=user, **defaults)

def create_coach(user, **extra_fields):
    defaults = {
        'name': 'Approved Coach',
        'age': 35,
        'citizenship': 'Japan',
        'club': 'Samurai FC',
        'license': 'Pro',
        'preffered_formation': '4-2-3-1',
        'average_term_as_coach': 5.0,
        'description': 'Experienced coach',
        'rate_per_session': Decimal('200000.00')
    }
    defaults.update(extra_fields)
    return Coach.objects.create(user=user, **defaults)

def create_report(reporter, coach, reason="Inappropriate behavior"):
    return Report.objects.create(reporter=reporter, coach=coach, reason=reason, created_at=timezone.now())


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = create_user('temuadmin', 'password123', user_type='customer')
        self.admin_user.is_superuser = True
        self.admin_user.is_staff = True
        self.admin_user.save()

    def test_given_no_user_when_accessing_dashboard_then_redirects_to_login(self):
        response = self.client.get(reverse('my_admin:dashboard_simple'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('my_admin:dashboard_simple')}")

    def test_given_admin_logged_in_when_accessing_dashboard_then_loads_template_and_context(self):
        self.client.login(username='temuadmin', password='password123')
        response = self.client.get(reverse('my_admin:dashboard_simple'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_simple.html')
        self.assertIn('reports', response.context)
        self.assertIn('pending_requests', response.context)


class ApproveCoachViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = create_user('admin', 'adminpass', user_type='customer')
        self.admin.is_superuser = True
        self.admin.save()
        self.user = create_user('coachuser', 'password123', user_type='coach')
        self.coach_req = create_coach_request(self.user)

    def test_given_valid_coach_request_when_posting_then_creates_coach_and_admin_action(self):
        self.client.force_login(self.admin)
        url = reverse('my_admin:approve_coach', args=[self.coach_req.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('my_admin:dashboard_simple'))
        self.coach_req.refresh_from_db()
        self.assertTrue(self.coach_req.approved)
        self.assertTrue(Coach.objects.filter(user=self.user).exists())
        self.assertTrue(AdminAction.objects.filter(action_type='APPROVE').exists())
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any('approved successfully' in str(m) for m in storage))

    def test_given_already_approved_coach_request_when_posting_then_shows_info_message(self):
        self.coach_req.approved = True
        self.coach_req.save()
        self.client.force_login(self.admin)
        url = reverse('my_admin:approve_coach', args=[self.coach_req.id])
        response = self.client.post(url)
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any('already approved' in str(m) for m in storage))


class RejectCoachViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = create_user('admin', 'adminpass', user_type='customer')
        self.admin.is_superuser = True
        self.admin.save()
        self.user = create_user('coachreject', 'password123', user_type='coach')
        self.coach_req = create_coach_request(self.user)

    def test_given_valid_request_when_rejected_then_request_deleted_and_user_reverted_to_customer(self):
        self.client.force_login(self.admin)
        url = reverse('my_admin:reject_coach', args=[self.coach_req.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('my_admin:dashboard_simple'))
        self.assertFalse(CoachRequest.objects.filter(pk=self.coach_req.id).exists())
        self.user.refresh_from_db()
        self.assertEqual(self.user.user_type, 'customer')
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any('rejected' in str(m) for m in storage))


class BanCoachViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = create_user('admin', 'adminpass', user_type='customer')
        self.admin.is_superuser = True
        self.admin.save()
        self.user = create_user('coachban', 'password123', user_type='coach')
        self.coach = create_coach(self.user)

    def test_given_valid_coach_when_banned_then_user_deleted_and_admin_action_created(self):
        self.client.force_login(self.admin)
        url = reverse('my_admin:ban_coach', args=[self.coach.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('my_admin:dashboard_simple'))
        self.assertFalse(User.objects.filter(username='coachban').exists())
        self.assertTrue(AdminAction.objects.filter(action_type='BAN_COACH').exists())
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any('banned and deleted' in str(m) for m in storage))


class DeleteReportViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = create_user('admin', 'adminpass', user_type='customer')
        self.admin.is_superuser = True
        self.admin.save()
        self.reporter = create_user('reporter', 'password123')
        self.coach_user = create_user('coachforreport', 'password123', user_type='coach')
        self.coach = create_coach(self.coach_user)
        self.report = create_report(self.reporter, self.coach)

    def test_given_existing_report_when_deleted_then_report_removed_and_admin_action_logged(self):
        self.client.force_login(self.admin)
        url = reverse('my_admin:delete_report', args=[self.report.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('my_admin:dashboard_simple'))
        self.assertFalse(Report.objects.filter(pk=self.report.id).exists())
        self.assertTrue(AdminAction.objects.filter(action_type='DELETE_REPORT').exists())
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any('deleted successfully' in str(m) for m in storage))
