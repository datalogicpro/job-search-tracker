import logging
import uuid
from dataclasses import asdict

from django.core.management.base import BaseCommand
from django.db import models, transaction

from config.log_format import run_id_var
from jobs.filters import is_unpaid, rejection_reason
from jobs.models import Job
from jobs.sources import SOURCES
from jobs.sources.base import JobData, build_session
from jobs.yc import fetch_yc_company_names, normalize_company

logger = logging.getLogger(__name__)

SOURCE_NAMES = [source.name for source in SOURCES]
FIELD_LIMITS = {
    field.name: field.max_length
    for field in Job._meta.concrete_fields
    if isinstance(field, models.CharField) and field.max_length
}


class Command(BaseCommand):
    help = "Fetch jobs from every source, filter them, and save the ones that pass."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=SOURCE_NAMES,
            help="Run only this one source.",
        )

    def handle(self, *args, **options):
        run_id = uuid.uuid4().hex[:12]
        token = run_id_var.set(run_id)
        try:
            self.run(run_id, options["source"])
        finally:
            run_id_var.reset(token)

    def run(self, run_id: str, source_name: str | None) -> None:
        session = build_session()
        yc_names = fetch_yc_company_names(session)
        selected = [s for s in SOURCES if source_name in (None, s.name)]
        totals = {"fetched": 0, "saved": 0, "rejected": 0, "failed_sources": 0}

        logger.info("fetch run started", extra={"run_id": run_id, "sources": len(selected)})

        for source_class in selected:
            source = source_class(session=session)
            try:
                jobs = source.fetch()
            except Exception:
                totals["failed_sources"] += 1
                logger.exception("source failed", extra={"run_id": run_id, "source": source.name})
                self.stderr.write(self.style.ERROR(f"{source.name}: failed (run {run_id})"))
                continue

            saved, rejected = self.save_jobs(jobs, yc_names, run_id)
            totals["fetched"] += len(jobs)
            totals["saved"] += saved
            totals["rejected"] += rejected
            self.stdout.write(f"{source.name}: {len(jobs)} fetched, {saved} saved, {rejected} rejected")

        logger.info("fetch run finished", extra={"run_id": run_id, **totals})
        self.stdout.write(
            self.style.SUCCESS(
                f"Run {run_id} done: {totals['fetched']} fetched, {totals['saved']} saved, "
                f"{totals['rejected']} rejected, {totals['failed_sources']} sources failed"
            )
        )

    @transaction.atomic
    def save_jobs(self, jobs: list[JobData], yc_names: set[str], run_id: str) -> tuple[int, int]:
        saved = 0
        rejected = 0
        for job in jobs:
            reason = rejection_reason(job)
            if reason:
                rejected += 1
                logger.debug(
                    "job rejected",
                    extra={
                        "run_id": run_id,
                        "source": job.source,
                        "external_id": job.external_id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "reason": reason,
                    },
                )
                continue

            fields = asdict(job)
            source = fields.pop("source")
            external_id = fields.pop("external_id")
            for name, limit in FIELD_LIMITS.items():
                if name in fields:
                    fields[name] = (fields[name] or "")[:limit]
            fields["is_yc_company"] = normalize_company(job.company) in yc_names
            fields["is_unpaid"] = is_unpaid(job)

            Job.objects.update_or_create(
                source=source,
                external_id=external_id,
                defaults=fields,
            )
            saved += 1
        return saved, rejected