from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser


@receiver(post_save, sender=CustomUser)
def user_created_handler(sender, instance, created, **kwargs):
    if created:
        from apps.tasks.email_tasks import send_welcome_email
        send_welcome_email.delay(instance.id)
