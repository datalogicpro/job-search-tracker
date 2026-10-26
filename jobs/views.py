from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from .models import Job
from .serializers import JobDetailSerializer, JobListSerializer


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    def get_serializer_class(self):
        if self.action == "retrieve":
            return JobDetailSerializer
        return JobListSerializer

    def get_queryset(self):
        queryset = Job.objects.filter(closed_at__isnull=True)
        params = self.request.query_params

        source = params.get("source")
        if source:
            queryset = queryset.filter(source=source)

        if params.get("yc") == "true":
            queryset = queryset.filter(is_yc_company=True)

        unpaid = params.get("unpaid")
        if unpaid == "true":
            queryset = queryset.filter(is_unpaid=True)
        elif unpaid == "false":
            queryset = queryset.filter(is_unpaid=False)

        search = params.get("q")
        if search:
            queryset = queryset.filter(title__icontains=search)

        days = params.get("days")
        if days:
            if not days.isdigit():
                raise ValidationError({"days": "Must be a whole number."})
            since = timezone.now() - timedelta(days=int(days))
            queryset = queryset.filter(posted_at__gte=since)

        return queryset