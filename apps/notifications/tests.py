from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import CustomUser
from .models import Notification
from .utils import create_notification


class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(email="notif@test.com", password="Pass123!")
        self.client.force_authenticate(user=self.user)

    def test_create_notification(self):
        notif = Notification.objects.create(
            user=self.user, title="Test", message="Test message"
        )
        self.assertEqual(Notification.objects.count(), 1)
        self.assertFalse(notif.is_read)

    def test_list_notifications(self):
        Notification.objects.create(user=self.user, title="N1", message="m1")
        Notification.objects.create(user=self.user, title="N2", message="m2")
        res = self.client.get(reverse("notification-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_mark_as_read(self):
        notif = Notification.objects.create(user=self.user, title="N1", message="m1")
        res = self.client.patch(reverse("notification-detail", kwargs={"pk": notif.pk}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_clear_read_notifications(self):
        Notification.objects.create(user=self.user, title="N1", message="m1", is_read=True)
        Notification.objects.create(user=self.user, title="N2", message="m2", is_read=False)
        res = self.client.delete(reverse("notification-clear"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["deleted"], 1)
        self.assertEqual(Notification.objects.count(), 1)
