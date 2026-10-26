import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from jobs.sources.jobicy import JobicySource

FIXTURE = Path(__file__).parent / "fixtures" / "jobicy.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fetch_with_fixture(monkeypatch):
    source = JobicySource()
    monkeypatch.setattr(source, "request", lambda method, url, **kwargs: FakeResponse(load_fixture()))
    return source.fetch()


def test_fetch_returns_every_job(monkeypatch):
    jobs = fetch_with_fixture(monkeypatch)
    assert [job.external_id for job in jobs] == ["150923", "156737", "149543"]


def test_parse_us_job_with_yearly_salary(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[0]

    assert job.source == "jobicy"
    assert job.title == "Junior Python Developer"
    assert job.company == "Harborview Health"
    assert job.url == "https://jobicy.com/jobs/150923-junior-python-developer"
    assert job.location == "USA"
    assert job.is_remote is True
    assert job.accepts_us is True
    assert job.seniority == "Entry-Level, Junior"
    assert job.employment_type == "Full-Time"
    assert job.salary_min == Decimal("77000")
    assert job.salary_max == Decimal("100000")
    assert job.salary_currency == "USD"
    assert job.posted_at == datetime(2026, 10, 24, 3, 45, 6, tzinfo=timezone.utc)


def test_parse_apac_job_without_salary(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[1]

    assert job.location == "APAC"
    assert job.accepts_us is False
    assert job.salary_min is None
    assert job.salary_max is None
    assert job.salary_currency == ""


def test_parse_anywhere_job(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[2]

    assert job.location == "Anywhere"
    assert job.accepts_us is True
    assert job.seniority == "Any"