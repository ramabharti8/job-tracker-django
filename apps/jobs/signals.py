from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Application


@receiver(pre_save, sender=Application)
def track_status_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Application.objects.get(pk=instance.pk)
            instance._previous_status = old.status
        except Application.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Application)
def application_status_changed(sender, instance, created, **kwargs):
    previous = getattr(instance, "_previous_status", None)

    if not created and previous and previous != instance.status:
        from apps.tasks.email_tasks import send_status_change_email
        send_status_change_email.delay(instance.id, previous, instance.status)

        from apps.notifications.utils import create_notification
        create_notification(
            user=instance.user,
            title="Application Status Updated",
            message=f'"{instance.job_title}" at {instance.company.name} moved to {instance.get_status_display()}.',
        )
