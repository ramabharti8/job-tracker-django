from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import CustomUser
from .models import Company, Application, InterviewRound
from django.utils import timezone
from datetime import timedelta


def make_user(email="user@test.com", password="StrongPass123!"):
    return CustomUser.objects.create_user(email=email, password=password)


class CompanyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("company-list")

    def test_create_company(self):
        res = self.client.post(self.url, {"name": "Google", "industry": "Tech"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Company.objects.count(), 1)

    def test_list_own_companies_only(self):
        other = make_user("other@test.com")
        Company.objects.create(name="OtherCo", user=other)
        Company.objects.create(name="MyCo", user=self.user)
        res = self.client.get(self.url)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["name"], "MyCo")


class ApplicationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.company = Company.objects.create(name="TestCorp", user=self.user)
        self.list_url = reverse("application-list")

    def _create_app(self, **kwargs):
        data = {"job_title": "Backend Engineer", "company": self.company.id, **kwargs}
        return self.client.post(self.list_url, data)

    def test_create_application(self):
        res = self._create_app()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 1)

    def test_default_status_is_applied(self):
        res = self._create_app()
        self.assertEqual(res.data["status"], Application.Status.APPLIED)

    def test_update_status(self):
        self._create_app()
        app = Application.objects.first()
        url = reverse("application-update-status", kwargs={"pk": app.pk})
        res = self.client.patch(url, {"status": Application.Status.SCREENING})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.status, Application.Status.SCREENING)

    def test_invalid_salary_range(self):
        res = self._create_app(salary_min=100000, salary_max=50000)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_endpoint(self):
        self._create_app()
        url = reverse("application-dashboard")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("total_applications", res.data)
        self.assertEqual(res.data["total_applications"], 1)

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class InterviewRoundTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.company = Company.objects.create(name="TechCo", user=self.user)
        self.app = Application.objects.create(
            user=self.user, company=self.company, job_title="SWE"
        )

    def test_create_interview(self):
        url = reverse("interview-list")
        data = {
            "application": self.app.id,
            "round_number": 1,
            "interview_type": InterviewRound.InterviewType.PHONE,
            "scheduled_at": (timezone.now() + timedelta(days=3)).isoformat(),
        }
        res = self.client.post(url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_upcoming_interviews(self):
        InterviewRound.objects.create(
            application=self.app,
            round_number=1,
            interview_type=InterviewRound.InterviewType.VIDEO,
            scheduled_at=timezone.now() + timedelta(days=2),
        )
        url = reverse("interview-upcoming")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
