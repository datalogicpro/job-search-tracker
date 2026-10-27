from django.contrib import admin

from .models import Application, Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "company",
        "source",
        "location",
        "is_unpaid",
        "is_yc_company",
        "posted_at",
        "applied_status",
    ]
    list_filter = ["source", "is_unpaid", "is_yc_company", "accepts_us", "seniority"]
    list_select_related = ["application"]
    search_fields = ["title", "company", "description"]
    ordering = ["-posted_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Applied")
    def applied_status(self, obj):
        application = getattr(obj, "application", None)
        return application.get_status_display() if application else "-"


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["job_title", "job_company", "status", "applied_at", "updated_at"]
    list_editable = ["status"]
    list_filter = ["status"]
    list_select_related = ["job"]
    search_fields = ["job__title", "job__company"]
    autocomplete_fields = ["job"]
    ordering = ["-applied_at"]

    @admin.display(description="Job", ordering="job__title")
    def job_title(self, obj):
        return obj.job.title

    @admin.display(description="Company", ordering="job__company")
    def job_company(self, obj):
        return obj.job.company