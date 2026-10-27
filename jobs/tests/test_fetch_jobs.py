import pytest

from jobs.management.commands.fetch_jobs import FIELD_LIMITS, Command
from jobs.models import Job
from jobs.sources.base import JobData


def make_job(**overrides) -> JobData:
    values = {
        "source": "jobicy",
        "external_id": "1",
        "title": "Junior Python Developer",
        "company": "Example Co",
        "url": "https://example.com/job/1",
        "is_remote": True,
        "accepts_us": True,
        "description": "Build APIs with Python and Django.",
    }
    values.update(overrides)
    return JobData(**values)


def test_field_limits_come_from_model():
    assert FIELD_LIMITS["seniority"] == 50
    assert FIELD_LIMITS["employment_type"] == 50
    assert FIELD_LIMITS["salary_currency"] == 3
    assert FIELD_LIMITS["url"] == 1000


@pytest.mark.django_db
def test_save_cuts_long_values_to_fit():
    job = make_job(seniority="Entry-Level, " * 10, employment_type="Full-Time, " * 10)

    saved, rejected = Command().save_jobs([job], set(), "testrun0000")

    assert (saved, rejected) == (1, 0)
    row = Job.objects.get(source="jobicy", external_id="1")
    assert len(row.seniority) == 50
    assert len(row.employment_type) == 50