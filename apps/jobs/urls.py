from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, ApplicationViewSet, ContactViewSet, InterviewRoundViewSet

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("applications", ApplicationViewSet, basename="application")
router.register("contacts", ContactViewSet, basename="contact")
router.register("interviews", InterviewRoundViewSet, basename="interview")

urlpatterns = [
    path("", include(router.urls)),
]
