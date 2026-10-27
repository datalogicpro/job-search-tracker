from datetime import timedelta

from django.core import signing
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from .applications import read_token
from .models import Application, Job
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

        applied = params.get("applied")
        if applied == "true":
            queryset = queryset.filter(application__isnull=False)
        elif applied == "false":
            queryset = queryset.filter(application__isnull=True)

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


@require_http_methods(["GET", "POST"])
def mark_applied(request, token):
    template = "jobs/mark_applied.html"
    try:
        job_id = read_token(token)
    except signing.SignatureExpired:
        return render(request, template, {"error": "This link has expired."}, status=400)
    except signing.BadSignature:
        return render(request, template, {"error": "This link is not valid."}, status=400)

    job = get_object_or_404(Job, pk=job_id)
    application = Application.objects.filter(job=job).first()
    if request.method == "POST" and application is None:
        application, _ = Application.objects.get_or_create(job=job)

    return render(request, template, {"job": job, "application": application})