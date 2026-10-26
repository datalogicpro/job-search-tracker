from rest_framework import serializers

from .models import Job

LIST_FIELDS = [
    "id",
    "source",
    "title",
    "company",
    "url",
    "location",
    "is_remote",
    "accepts_us",
    "seniority",
    "employment_type",
    "salary_min",
    "salary_max",
    "salary_currency",
    "is_unpaid",
    "posted_at",
    "is_yc_company",
    "first_seen_at",
]


class JobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = LIST_FIELDS
        read_only_fields = LIST_FIELDS


class JobDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [*LIST_FIELDS, "description", "last_seen_at", "closed_at"]
        read_only_fields = fields
        