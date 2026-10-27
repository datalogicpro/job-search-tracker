import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.db.models import F
from django.utils import timezone

from jobs.filters import plain_text
from jobs.models import Job

logger = logging.getLogger(__name__)

PREVIEW_LENGTH = 300


def format_salary(job: Job) -> str:
    if job.salary_min is None and job.salary_max is None:
        return "not listed"
    low = f"${job.salary_min:,.0f}" if job.salary_min is not None else ""
    high = f"${job.salary_max:,.0f}" if job.salary_max is not None else ""
    amount = f"{low} to {high}" if low and high else low or high
    return f"{amount} {job.salary_currency}".strip()


def format_preview(description: str) -> str:
    text = " ".join(plain_text(description).split())
    if len(text) <= PREVIEW_LENGTH:
        return text
    cut = text[:PREVIEW_LENGTH].rsplit(" ", 1)[0]
    return f"{cut}..."


def format_job(number: int, job: Job) -> str:
    tags = []
    if job.is_yc_company:
        tags.append("[YC]")
    if job.is_unpaid:
        tags.append("[UNPAID]")
    tag_text = f" {' '.join(tags)}" if tags else ""
    posted = job.posted_at.strftime("%b %d, %Y") if job.posted_at else "unknown"

    lines = [
        f"{number}. {job.title} at {job.company}{tag_text}",
        f"   Location: {job.location or 'not listed'}",
        f"   Type: {job.employment_type or 'not listed'}",
        f"   Level: {job.seniority or 'not listed'}",
        f"   Salary: {format_salary(job)}",
        f"   Posted: {posted}",
        f"   Source: {job.get_source_display()}",
    ]
    preview = format_preview(job.description)
    if preview:
        lines.append(f"   Preview: {preview}")
    lines.append(f"   Apply: {job.url}")
    return "\n".join(lines)


def build_body(jobs: list[Job]) -> str:
    sections = [format_job(number, job) for number, job in enumerate(jobs, start=1)]
    footer = "Every link goes to the original posting on its source."
    return "\n\n".join(sections + [footer])


class Command(BaseCommand):
    help = "Email every open job not sent in a digest yet, then mark those jobs as sent."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the email instead of sending it, and mark nothing as sent.",
        )

    def handle(self, *args, **options):
        if not settings.DIGEST_TO:
            raise CommandError("DIGEST_TO is not set in .env.")

        jobs = list(
            Job.objects.filter(closed_at__isnull=True, digest_sent_at__isnull=True).order_by(
                F("posted_at").desc(nulls_last=True)
            )
        )
        if not jobs:
            logger.info("digest skipped, no new jobs")
            self.stdout.write("No new jobs. Nothing sent.")
            return

        subject = f"{len(jobs)} new job{'s' if len(jobs) != 1 else ''} from job-search-tracker"
        body = build_body(jobs)

        if options["dry_run"]:
            self.stdout.write(subject)
            self.stdout.write("")
            self.stdout.write(body)
            return

        sent = EmailMessage(subject=subject, body=body, to=[settings.DIGEST_TO]).send()
        if not sent:
            raise CommandError("The digest email was not sent. No jobs were marked as sent.")

        Job.objects.filter(pk__in=[job.pk for job in jobs]).update(digest_sent_at=timezone.now())
        logger.info("digest sent", extra={"jobs": len(jobs)})
        self.stdout.write(self.style.SUCCESS(f"Digest sent with {len(jobs)} jobs."))