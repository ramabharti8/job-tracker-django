from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from .models import Company, Application, Contact, InterviewRound
from .serializers import (
    CompanySerializer, ApplicationListSerializer, ApplicationDetailSerializer,
    ContactSerializer, InterviewRoundSerializer, DashboardSerializer,
)
from .filters import ApplicationFilter, CompanyFilter


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    filterset_class = CompanyFilter
    search_fields = ["name", "industry"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return Company.objects.filter(user=self.request.user).annotate(
            application_count=Count("applications")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_class = ApplicationFilter
    search_fields = ["job_title", "company__name", "location", "notes"]
    ordering_fields = ["applied_date", "created_at", "status", "excitement_level"]

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).select_related("company").annotate(
            interview_count=Count("interviews")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ApplicationListSerializer
        return ApplicationDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        old_status = self.get_object().status
        instance = serializer.save()
        if old_status != instance.status:
            cache.delete(f"dashboard_{self.request.user.id}")

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        cache_key = f"dashboard_{request.user.id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        qs = Application.objects.filter(user=request.user)
        total = qs.count()

        by_status = {
            s: qs.filter(status=s).count()
            for s in Application.Status.values
        }

        responded = qs.exclude(status=Application.Status.APPLIED).count()
        interviewed = qs.filter(
            status__in=[Application.Status.PHONE, Application.Status.TECHNICAL,
                        Application.Status.OFFER, Application.Status.REJECTED]
        ).count()
        offers = qs.filter(status=Application.Status.OFFER).count()

        now = timezone.now()
        upcoming = InterviewRound.objects.filter(
            application__user=request.user,
            scheduled_at__gte=now,
            scheduled_at__lte=now + timedelta(days=7),
            outcome=InterviewRound.Outcome.PENDING,
        ).select_related("application", "application__company")[:5]

        recent = qs.order_by("-created_at")[:5]

        data = {
            "total_applications": total,
            "by_status": by_status,
            "response_rate": round((responded / total * 100), 1) if total else 0.0,
            "interview_conversion": round((interviewed / total * 100), 1) if total else 0.0,
            "offer_rate": round((offers / total * 100), 1) if total else 0.0,
            "avg_days_to_response": None,
            "upcoming_interviews": InterviewRoundSerializer(upcoming, many=True).data,
            "recent_applications": ApplicationListSerializer(recent, many=True).data,
        }

        cache.set(cache_key, data, timeout=300)
        return Response(data)

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        application = self.get_object()
        new_status = request.data.get("status")
        if new_status not in Application.Status.values:
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        application.status = new_status
        application.save()
        cache.delete(f"dashboard_{request.user.id}")
        return Response(ApplicationDetailSerializer(application).data)


class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(application__user=self.request.user)


class InterviewRoundViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewRoundSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ["scheduled_at", "round_number"]

    def get_queryset(self):
        return InterviewRound.objects.filter(
            application__user=self.request.user
        ).select_related("application", "application__company")

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        now = timezone.now()
        qs = self.get_queryset().filter(
            scheduled_at__gte=now,
            scheduled_at__lte=now + timedelta(days=7),
            outcome=InterviewRound.Outcome.PENDING,
        )
        return Response(InterviewRoundSerializer(qs, many=True).data)
