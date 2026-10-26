from django.contrib import admin

from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "source", "location", "is_unpaid", "is_yc_company", "posted_at"]
    list_filter = ["source", "is_unpaid", "is_yc_company", "accepts_us", "seniority"]
    search_fields = ["title", "company", "description"]
    ordering = ["-posted_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False