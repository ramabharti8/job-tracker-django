from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification


def create_notification(user, title, message, notification_type="system"):
    notif = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
    )

    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                "type": "send_notification",
                "id": notif.id,
                "title": notif.title,
                "message": notif.message,
                "notification_type": notif.notification_type,
                "created_at": notif.created_at.isoformat(),
            },
        )
    except Exception:
        pass

    return notif
