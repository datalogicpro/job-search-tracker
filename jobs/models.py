from django.db import models


class Job(models.Model):
    class Source(models.TextChoices):
        HIMALAYAS = "himalayas", "Himalayas"
        REMOTE_OK = "remoteok", "Remote OK"
        WE_WORK_REMOTELY = "weworkremotely", "We Work Remotely"
        JOBICY = "jobicy", "Jobicy"
        THE_MUSE = "themuse", "The Muse"
        HACKER_NEWS = "hackernews", "Hacker News"
        JSEARCH = "jsearch", "JSearch"
        THEIRSTACK = "theirstack", "TheirStack"

    source = models.CharField(max_length=32, choices=Source.choices)
    external_id = models.CharField(max_length=255)
    title = models.CharField(max_length=300)
    company = models.CharField(max_length=300)
    url = models.URLField(max_length=1000)
    location = models.CharField(max_length=300, blank=True)
    is_remote = models.BooleanField(default=False)
    accepts_us = models.BooleanField(default=False)
    seniority = models.CharField(max_length=50, blank=True)
    employment_type = models.CharField(max_length=50, blank=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, blank=True)
    is_unpaid = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    is_yc_company = models.BooleanField(default=False)
    is_recruiting_agency = models.BooleanField(default=False)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    digest_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-posted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                name="unique_job_per_source",
            ),
        ]
        indexes = [
            models.Index(fields=["posted_at"]),
            models.Index(fields=["is_remote", "accepts_us"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.company} ({self.get_source_display()})"