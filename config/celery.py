import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("jobtracker")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "send-interview-reminders-daily": {
        "task": "apps.tasks.email_tasks.send_interview_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "send-weekly-summary": {
        "task": "apps.tasks.email_tasks.send_weekly_summary",
        "schedule": crontab(day_of_week="monday", hour=9, minute=0),
    },
}
