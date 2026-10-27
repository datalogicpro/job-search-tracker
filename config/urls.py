from django.contrib import admin
from django.urls import include, path

from config.health import health
from jobs.views import mark_applied

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("jobs.urls")),
    path("applications/mark/<str:token>/", mark_applied, name="mark-applied"),
    path("health/", health),
]