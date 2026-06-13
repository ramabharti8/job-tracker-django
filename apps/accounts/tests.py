from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import CustomUser


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.profile_url = reverse("profile")

    def test_register_success(self):
        data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertTrue(CustomUser.objects.filter(email="test@example.com").exists())

    def test_register_password_mismatch(self):
        data = {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "StrongPass123!",
            "password2": "WrongPass456!",
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        CustomUser.objects.create_user(email="login@example.com", password="StrongPass123!")
        response = self.client.post(self.login_url, {"email": "login@example.com", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_profile_requires_auth(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_authenticated(self):
        user = CustomUser.objects.create_user(email="profile@example.com", password="StrongPass123!")
        self.client.force_authenticate(user=user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "profile@example.com")
