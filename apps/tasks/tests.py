from django.test import TestCase
from unittest.mock import patch
from apps.accounts.models import CustomUser
from apps.jobs.models import Company, Application, InterviewRound
from django.utils import timezone
from datetime import timedelta
from .email_tasks import send_interview_reminders, send_weekly_summary


class CeleryTaskTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="task@test.com", password="Pass123!", full_name="Task User"
        )
        self.company = Company.objects.create(name="TaskCorp", user=self.user)
        self.app = Application.objects.create(
            user=self.user, company=self.company, job_title="Backend Engineer"
        )

    @patch("apps.tasks.email_tasks.send_mail")
    def test_interview_reminder_task(self, mock_send):
        InterviewRound.objects.create(
            application=self.app,
            round_number=1,
            interview_type=InterviewRound.InterviewType.PHONE,
            scheduled_at=timezone.now() + timedelta(hours=12),
        )
        result = send_interview_reminders()
        self.assertIn("1", result)
        mock_send.assert_called_once()

    @patch("apps.tasks.email_tasks.send_mail")
    def test_weekly_summary_skips_inactive_users(self, mock_send):
        self.user.is_active = False
        self.user.save()
        send_weekly_summary()
        mock_send.assert_not_called()

    @patch("apps.tasks.email_tasks.send_mail")
    def test_weekly_summary_sent_for_active_users(self, mock_send):
        send_weekly_summary()
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        self.assertIn("Task User", call_args[1]["message"])
