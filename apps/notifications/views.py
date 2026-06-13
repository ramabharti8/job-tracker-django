from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        unread_only = self.request.query_params.get("unread")
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs


class NotificationDetailView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def patch(self, request, *args, **kwargs):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def clear_read_notifications(request):
    deleted, _ = Notification.objects.filter(user=request.user, is_read=True).delete()
    return Response({"deleted": deleted}, status=status.HTTP_200_OK)
