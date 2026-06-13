from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    from apps.accounts.models import CustomUser
    try:
        user = CustomUser.objects.get(pk=user_id)
        send_mail(
            subject="Welcome to Job Tracker!",
            message=f"Hi {user.display_name},\n\nWelcome to Job Tracker! Start tracking your applications today.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except CustomUser.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_status_change_email(self, application_id, old_status, new_status):
    from apps.jobs.models import Application
    try:
        app = Application.objects.select_related("user", "company").get(pk=application_id)
        send_mail(
            subject=f"Application Update: {app.job_title} at {app.company.name}",
            message=(
                f"Hi {app.user.display_name},\n\n"
                f'Your application for "{app.job_title}" at {app.company.name} '
                f"has moved from {old_status.upper()} to {new_status.upper()}.\n\n"
                f"Log in to Job Tracker to see more details."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[app.user.email],
            fail_silently=False,
        )
    except Application.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_interview_reminders():
    from apps.jobs.models import InterviewRound
    from apps.notifications.utils import create_notification

    now = timezone.now()
    tomorrow = now + timedelta(hours=24)

    upcoming = InterviewRound.objects.filter(
        scheduled_at__gte=now,
        scheduled_at__lte=tomorrow,
        outcome=InterviewRound.Outcome.PENDING,
    ).select_related("application__user", "application__company")

    for interview in upcoming:
        user = interview.application.user
        company = interview.application.company.name
        job = interview.application.job_title

        send_mail(
            subject=f"Interview Reminder: {job} at {company}",
            message=(
                f"Hi {user.display_name},\n\n"
                f"Reminder: You have a {interview.get_interview_type_display()} interview "
                f"for {job} at {company} scheduled at {interview.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')}.\n\n"
                f"Good luck!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        create_notification(
            user=user,
            title="Interview Reminder",
            message=f"Your interview for {job} at {company} is in less than 24 hours.",
            notification_type="interview",
        )

    return f"Sent {upcoming.count()} reminders"


@shared_task
def send_weekly_summary():
    from apps.accounts.models import CustomUser
    from apps.jobs.models import Application
    from django.db.models import Count

    users = CustomUser.objects.filter(is_active=True)
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    for user in users:
        apps_this_week = Application.objects.filter(user=user, created_at__gte=week_ago)
        if not apps_this_week.exists():
            continue

        total = Application.objects.filter(user=user).count()
        offers = Application.objects.filter(user=user, status="offer").count()

        send_mail(
            subject="Your Weekly Job Search Summary",
            message=(
                f"Hi {user.display_name},\n\n"
                f"Here's your job search summary for this week:\n\n"
                f"  • New applications this week: {apps_this_week.count()}\n"
                f"  • Total applications: {total}\n"
                f"  • Offers received: {offers}\n\n"
                f"Keep going — consistency is key!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
