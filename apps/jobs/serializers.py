from rest_framework import serializers
from .models import Company, Application, Contact, InterviewRound


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class InterviewRoundSerializer(serializers.ModelSerializer):
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = InterviewRound
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class ApplicationListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    days_since_applied = serializers.IntegerField(read_only=True)
    salary_range = serializers.CharField(read_only=True)
    interview_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = (
            "id", "job_title", "company", "company_name", "status", "work_mode",
            "location", "salary_range", "applied_date", "days_since_applied",
            "referral", "excitement_level", "interview_count", "created_at",
        )


class ApplicationDetailSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)
    interviews = InterviewRoundSerializer(many=True, read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    salary_range = serializers.CharField(read_only=True)
    days_since_applied = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def validate(self, attrs):
        if attrs.get("salary_min") and attrs.get("salary_max"):
            if attrs["salary_min"] > attrs["salary_max"]:
                raise serializers.ValidationError({"salary_min": "Minimum salary cannot exceed maximum."})
        return attrs


class CompanySerializer(serializers.ModelSerializer):
    application_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")


class DashboardSerializer(serializers.Serializer):
    total_applications = serializers.IntegerField()
    by_status = serializers.DictField()
    response_rate = serializers.FloatField()
    interview_conversion = serializers.FloatField()
    offer_rate = serializers.FloatField()
    avg_days_to_response = serializers.FloatField(allow_null=True)
    upcoming_interviews = InterviewRoundSerializer(many=True)
    recent_applications = ApplicationListSerializer(many=True)
