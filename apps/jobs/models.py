from django.db import models
from django.conf import settings
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    class Size(models.TextChoices):
        STARTUP = "startup", "Startup (1-50)"
        SMALL = "small", "Small (51-200)"
        MID = "mid", "Mid-size (201-1000)"
        ENTERPRISE = "enterprise", "Enterprise (1000+)"

    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=20, choices=Size.choices, blank=True)
    notes = models.TextField(blank=True)
    glassdoor_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="companies")

    class Meta:
        verbose_name_plural = "Companies"
        unique_together = ("name", "user")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Application(TimeStampedModel):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        SCREENING = "screening", "Screening"
        PHONE = "phone", "Phone Interview"
        TECHNICAL = "technical", "Technical Interview"
        OFFER = "offer", "Offer Received"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    class WorkMode(models.TextChoices):
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"
        ONSITE = "onsite", "On-site"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="applications")
    job_title = models.CharField(max_length=200)
    job_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    work_mode = models.CharField(max_length=10, choices=WorkMode.choices, blank=True)
    location = models.CharField(max_length=150, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    applied_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    job_description = models.TextField(blank=True)
    resume_version = models.CharField(max_length=50, blank=True)
    referral = models.BooleanField(default=False)
    referral_name = models.CharField(max_length=100, blank=True)
    excitement_level = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5 scale")

    class Meta:
        ordering = ["-applied_date", "-created_at"]

    def __str__(self):
        return f"{self.job_title} at {self.company.name} [{self.status}]"

    @property
    def days_since_applied(self):
        return (timezone.now().date() - self.applied_date).days

    @property
    def salary_range(self):
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,} – ${self.salary_max:,}"
        return None


class Contact(TimeStampedModel):
    class ContactRole(models.TextChoices):
        RECRUITER = "recruiter", "Recruiter"
        HIRING_MANAGER = "hiring_manager", "Hiring Manager"
        ENGINEER = "engineer", "Engineer"
        HR = "hr", "HR"
        OTHER = "other", "Other"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ContactRole.choices, default=ContactRole.RECRUITER)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) — {self.application.company.name}"


class InterviewRound(TimeStampedModel):
    class InterviewType(models.TextChoices):
        PHONE = "phone", "Phone Screen"
        VIDEO = "video", "Video Call"
        TECHNICAL = "technical", "Technical"
        SYSTEM_DESIGN = "system_design", "System Design"
        BEHAVIORAL = "behavioral", "Behavioral"
        ONSITE = "onsite", "On-site"
        TAKE_HOME = "take_home", "Take-home Assignment"

    class Outcome(models.TextChoices):
        PENDING = "pending", "Pending"
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="interviews")
    round_number = models.PositiveSmallIntegerField(default=1)
    interview_type = models.CharField(max_length=20, choices=InterviewType.choices)
    scheduled_at = models.DateTimeField()
    duration_mins = models.PositiveSmallIntegerField(default=60)
    interviewer = models.CharField(max_length=150, blank=True)
    location_or_link = models.CharField(max_length=300, blank=True)
    preparation_notes = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    outcome = models.CharField(max_length=10, choices=Outcome.choices, default=Outcome.PENDING)

    class Meta:
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"Round {self.round_number} — {self.get_interview_type_display()} for {self.application}"

    @property
    def is_upcoming(self):
        return self.scheduled_at > timezone.now() and self.outcome == self.Outcome.PENDING
