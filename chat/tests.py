import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal

from .models import Message
from coaches_book_catalog.models import Coach, Booking
from scheduler.models import Jadwal

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
    coach = Coach.objects.get(user=user)
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

def create_jadwal(coach, tanggal_offset_days, jam_mulai, jam_selesai, is_booked=False):
    tanggal = timezone.now().date() + datetime.timedelta(days=tanggal_offset_days)
    mulai = datetime.time.fromisoformat(jam_mulai)
    selesai = datetime.time.fromisoformat(jam_selesai)
    return Jadwal.objects.create(
        coach=coach, tanggal=tanggal, jam_mulai=mulai, jam_selesai=selesai, is_booked=is_booked
    )

def create_booking(customer, jadwal):
    return Booking.objects.create(customer=customer, jadwal=jadwal)

def create_message(sender, receiver, content):
    return Message.objects.create(sender=sender, receiver=receiver, content=content)

class MessageModelTests(TestCase):
    def setUp(self):
        self.sender = create_user('sender_user', 'password123')
        self.receiver = create_user('receiver_user', 'password123')

    def test_given_message_object_when_converted_to_string_then_returns_correct_format(self):
        msg = create_message(self.sender, self.receiver, "Test Content")
        msg_str = str(msg)
        self.assertEqual(msg_str, "From sender_user to receiver_user")

class ChatListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer1 = create_user('customer1', 'password123', user_type='customer')
        self.customer2 = create_user('customer2', 'password123', user_type='customer')
        self.coach1_user = create_user('coach1', 'password123', user_type='coach')
        self.coach2_user = create_user('coach2', 'password123', user_type='coach')
        self.pending_coach_user = create_user('pending_coach', 'password123', user_type='coach')
        self.superuser = create_user('super_admin', 'password123', is_superuser=True)
        self.coach1 = Coach.objects.get(user=self.coach_user1)
        self.coach2 = Coach.objects.get(user=self.coach_user2)
        pending_coach_profile = Coach.objects.filter(user=self.pending_coach_user)
        if pending_coach_profile.exists():
            pending_coach_profile.delete()
        self.jadwal = create_jadwal(self.coach1, 1, "10:00", "11:00")
        create_booking(self.customer1, self.jadwal)
        create_message(self.customer2, self.coach1_user, "Halo coach")
        self.url = reverse('chat_list')

    def test_given_unauthenticated_user_when_accessing_list_then_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_given_superuser_when_accessing_list_then_shows_all_approved_coaches(self):
        self.client.login(username='super_admin', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat_list.html')
        self.assertIn(self.coach_user1, response.context['users_list'])
        self.assertIn(self.coach_user2, response.context['users_list'])
        self.assertNotIn(self.pending_coach_user, response.context['users_list'])

    def test_given_approved_coach_when_accessing_list_then_shows_booked_and_messaged_customers(self):
        self.client.login(username='coach1', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        users_list = response.context['users_list']
        self.assertEqual(users_list.count(), 2)
        self.assertIn(self.customer1, users_list)
        self.assertIn(self.customer2, users_list)
        self.assertNotIn(self.coach1_user, users_list)

    def test_given_approved_coach_with_no_contacts_when_accessing_list_then_shows_empty_list(self):
        self.client.login(username='coach2', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['users_list'].count(), 0)

    def test_given_customer_when_accessing_list_then_shows_all_approved_coaches(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        users_list = response.context['users_list']
        self.assertIn(self.coach_user1, users_list)
        self.assertIn(self.coach_user2, users_list)
        self.assertNotIn(self.pending_coach_user, users_list)

    def test_given_pending_coach_when_accessing_list_then_shows_empty_list_and_warning(self):
        self.client.login(username='pending_coach', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['users_list'].count(), 0)
        storage = messages.get_messages(response.wsgi_request)
        self.assertTrue(any(message.level == messages.WARNING for message in storage))

    def test_given_customer_when_searching_then_returns_filtered_list(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(self.url, {'q': 'coach1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['users_list'].count(), 1)
        self.assertIn(self.coach_user1, response.context['users_list'])

    def test_given_customer_when_accessing_via_ajax_then_returns_partial_template(self):
        self.client.login(username='customer1', password='password123')
        response = self.client.get(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat_user_list_partial.html')

class ChatRoomViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.sender = create_user('sender', 'password123')
        self.receiver = create_user('receiver', 'password123')
        self.url = reverse('chat_room', args=[self.receiver.id])
        self.old_message_time = timezone.now() - datetime.timedelta(minutes=10)

    def test_given_unauthenticated_user_when_accessing_room_then_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_given_user_when_accessing_own_chat_room_then_redirects_to_list(self):
        self.client.login(username='sender', password='password123')
        own_url = reverse('chat_room', args=[self.sender.id])
        response = self.client.get(own_url)
        self.assertRedirects(response, reverse('chat_list'))

    def test_given_user_when_viewing_room_via_get_then_marks_messages_read(self):
        msg = create_message(self.receiver, self.sender, "Unread message")
        self.assertFalse(msg.is_read)
        self.client.login(username='sender', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat_room.html')
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
        self.assertIn(msg, response.context['message_list'])

    def test_given_user_when_sending_message_via_ajax_post_then_creates_message(self):
        self.client.login(username='sender', password='password123')
        response = self.client.post(
            self.url, 
            {'content': 'New message'}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.content)
        self.assertTrue(json_data['success'])
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().content, 'New message')

    def test_given_user_when_sending_empty_message_via_ajax_post_then_returns_400(self):
        self.client.login(username='sender', password='password123')
        response = self.client.post(
            self.url, 
            {'content': ''}, 
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)

    def test_given_message_owner_when_editing_message_via_ajax_put_then_updates_message(self):
        msg = create_message(self.sender, self.receiver, "Original content")
        self.client.login(username='sender', password='password123')
        response = self.client.put(
            self.url, 
            json.dumps({'message_id': msg.id, 'content': 'Edited content'}), 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['success'])
        msg.refresh_from_db()
        self.assertEqual(msg.content, 'Edited content')

    def test_given_user_when_editing_message_after_timeout_via_ajax_put_then_returns_403(self):
        msg = create_message(self.sender, self.receiver, "Old content")
        msg.timestamp = self.old_message_time
        msg.save()
        self.client.login(username='sender', password='password123')
        response = self.client.put(
            self.url, 
            json.dumps({'message_id': msg.id, 'content': 'Edited content'}), 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('Waktu edit sudah habis', json.loads(response.content)['error'])

    def test_given_non_owner_when_editing_message_via_ajax_put_then_returns_404(self):
        msg = create_message(self.receiver, self.sender, "Other user's message")
        self.client.login(username='sender', password='password123')
        response = self.client.put(
            self.url, 
            json.dumps({'message_id': msg.id, 'content': 'Edited content'}), 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)

    def test_given_message_owner_when_deleting_message_via_ajax_delete_then_deletes_message(self):
        msg = create_message(self.sender, self.receiver, "To be deleted")
        self.client.login(username='sender', password='password123')
        response = self.client.delete(
            self.url, 
            json.dumps({'message_id': msg.id}), 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['success'])
        self.assertEqual(Message.objects.count(), 0)

    def test_given_user_when_deleting_message_after_timeout_via_ajax_delete_then_returns_403(self):
        msg = create_message(self.sender, self.receiver, "Old message")
        msg.timestamp = self.old_message_time
        msg.save()
        self.client.login(username='sender', password='password123')
        response = self.client.delete(
            self.url, 
            json.dumps({'message_id': msg.id}), 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('Waktu hapus sudah habis', json.loads(response.content)['error'])

    def test_given_non_owner_when_deleting_message_via_ajax_delete_then_returns_404(self):
        msg = create_message(self.receiver, self.sender, "Other user's message")
        self.client.login(username='sender', password='password123')
        response = self.client.delete(
            self.url, 
            json.dumps({'message_id': msg.id}), 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 404)

    def test_given_user_when_using_invalid_method_via_ajax_then_returns_405(self):
        self.client.login(username='sender', password='password123')
        response = self.client.patch(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 405)

    def test_given_user_when_editing_with_bad_json_then_returns_400(self):
        self.client.login(username='sender', password='password123')
        response = self.client.put(
            self.url, 
            'not json', 
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
