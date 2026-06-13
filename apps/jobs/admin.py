from django.contrib import admin
from django.utils.html import format_html
from .models import Company, Application, Contact, InterviewRound


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ("name", "role", "email", "linkedin_url")


class InterviewRoundInline(admin.TabularInline):
    model = InterviewRound
    extra = 0
    fields = ("round_number", "interview_type", "scheduled_at", "outcome")
    readonly_fields = ("round_number",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "size", "user", "created_at")
    list_filter = ("size", "industry")
    search_fields = ("name", "industry")
    ordering = ("name",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "job_title", "company", "user", "colored_status",
        "work_mode", "applied_date", "excitement_level",
    )
    list_filter = ("status", "work_mode", "referral", "applied_date")
    search_fields = ("job_title", "company__name", "user__email")
    ordering = ("-applied_date",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [ContactInline, InterviewRoundInline]
    actions = ["mark_rejected", "mark_withdrawn"]

    def colored_status(self, obj):
        colors = {
            "applied": "#3498db",
            "screening": "#f39c12",
            "phone": "#9b59b6",
            "technical": "#e67e22",
            "offer": "#27ae60",
            "rejected": "#e74c3c",
            "withdrawn": "#95a5a6",
        }
        color = colors.get(obj.status, "#000")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )
    colored_status.short_description = "Status"

    @admin.action(description="Mark selected as Rejected")
    def mark_rejected(self, request, queryset):
        queryset.update(status=Application.Status.REJECTED)

    @admin.action(description="Mark selected as Withdrawn")
    def mark_withdrawn(self, request, queryset):
        queryset.update(status=Application.Status.WITHDRAWN)


@admin.register(InterviewRound)
class InterviewRoundAdmin(admin.ModelAdmin):
    list_display = ("application", "round_number", "interview_type", "scheduled_at", "colored_outcome")
    list_filter = ("interview_type", "outcome")
    search_fields = ("application__job_title", "application__company__name")

    def colored_outcome(self, obj):
        colors = {"pending": "#f39c12", "passed": "#27ae60", "failed": "#e74c3c"}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.outcome, "#000"),
            obj.get_outcome_display(),
        )
    colored_outcome.short_description = "Outcome"


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "email", "application")
    list_filter = ("role",)
    search_fields = ("name", "email", "application__company__name")
