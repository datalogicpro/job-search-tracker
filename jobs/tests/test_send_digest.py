from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO

import pytest
from django.core import mail
from django.core.management import CommandError, call_command

from jobs.management.commands.send_digest import PREVIEW_LENGTH, format_preview, format_salary
from jobs.models import Job

DIGEST_TO = "digest@example.com"


def make_job(external_id: str, **overrides) -> Job:
    values = {
        "source": "jobicy",
        "external_id": external_id,
        "title": f"Junior Python Developer {external_id}",
        "company": "Example Co",
        "url": f"https://jobicy.com/jobs/{external_id}",
        "location": "USA",
        "employment_type": "Full-Time",
        "seniority": "Entry-Level",
        "description": "<p>Build <strong>Python</strong> APIs.</p>",
        "posted_at": datetime(2026, 10, 20, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return Job.objects.create(**values)


@pytest.fixture
def digest_settings(settings):
    settings.DIGEST_TO = DIGEST_TO
    settings.DEFAULT_FROM_EMAIL = "sender@example.com"
    return settings


@pytest.mark.django_db
def test_sends_new_open_jobs_and_marks_them(digest_settings):
    make_job("1")
    make_job("2", is_yc_company=True)
    make_job("3", closed_at=datetime(2026, 10, 21, tzinfo=timezone.utc))
    make_job("4", digest_sent_at=datetime(2026, 10, 21, tzinfo=timezone.utc))

    call_command("send_digest", stdout=StringIO())

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == [DIGEST_TO]
    assert message.subject == "2 new jobs from job-search-tracker"
    assert "Junior Python Developer 1" in message.body
    assert "Junior Python Developer 2 at Example Co [YC]" in message.body
    assert "Junior Python Developer 3" not in message.body
    assert "Junior Python Developer 4" not in message.body
    assert "Source: Jobicy" in message.body
    assert Job.objects.filter(digest_sent_at__isnull=True, closed_at__isnull=True).count() == 0


@pytest.mark.django_db
def test_email_shows_type_level_and_preview(digest_settings):
    make_job("1")

    call_command("send_digest", stdout=StringIO())

    body = mail.outbox[0].body
    assert "Type: Full-Time" in body
    assert "Level: Entry-Level" in body
    assert "Preview: Build Python APIs." in body


@pytest.mark.django_db
def test_sends_nothing_without_new_jobs(digest_settings):
    out = StringIO()

    call_command("send_digest", stdout=out)

    assert getattr(mail, "outbox", []) == []
    assert "No new jobs" in out.getvalue()


@pytest.mark.django_db
def test_dry_run_sends_and_marks_nothing(digest_settings):
    make_job("1")
    out = StringIO()

    call_command("send_digest", "--dry-run", stdout=out)

    assert getattr(mail, "outbox", []) == []
    assert "Junior Python Developer 1" in out.getvalue()
    assert Job.objects.get(external_id="1").digest_sent_at is None


@pytest.mark.django_db
def test_stops_without_digest_to(settings):
    settings.DIGEST_TO = ""

    with pytest.raises(CommandError, match="DIGEST_TO"):
        call_command("send_digest", stdout=StringIO())


@pytest.mark.parametrize(
    ("salary_min", "salary_max", "currency", "expected"),
    [
        (Decimal("60000"), Decimal("80000"), "USD", "$60,000 to $80,000 USD"),
        (Decimal("60000"), None, "USD", "$60,000 USD"),
        (None, None, "", "not listed"),
    ],
)
def test_format_salary(salary_min, salary_max, currency, expected):
    job = Job(salary_min=salary_min, salary_max=salary_max, salary_currency=currency)
    assert format_salary(job) == expected


def test_preview_keeps_short_description_whole():
    assert format_preview("<p>Write   Python\nscripts.</p>") == "Write Python scripts."


def test_preview_cuts_long_description_at_a_word():
    preview = format_preview("python " * 100)

    assert preview.endswith("...")
    assert len(preview) <= PREVIEW_LENGTH + 3
    assert not preview.removesuffix("...").endswith(" ")


def test_preview_of_empty_description_is_empty():
    assert format_preview("") == ""