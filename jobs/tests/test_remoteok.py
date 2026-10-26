import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from jobs.sources.remoteok import RemoteOKSource

FIXTURE = Path(__file__).parent / "fixtures" / "remoteok.json"


def load_fixture() -> list:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fetch_with_fixture(monkeypatch):
    source = RemoteOKSource()
    monkeypatch.setattr(source, "request", lambda method, url, **kwargs: FakeResponse(load_fixture()))
    return source.fetch()


def test_fetch_skips_legal_notice_and_non_python_jobs(monkeypatch):
    jobs = fetch_with_fixture(monkeypatch)
    assert [job.external_id for job in jobs] == ["1137557", "1137540"]


def test_parse_worldwide_job_with_salary(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[0]

    assert job.source == "remoteok"
    assert job.title == "Senior DevOps Engineer"
    assert job.company == "Lemon.io"
    assert job.url == "https://remoteOK.com/remote-jobs/remote-senior-devops-engineer-lemon-io-1137557"
    assert job.location == "Worldwide"
    assert job.accepts_us is True
    assert job.salary_min == Decimal("50000")
    assert job.salary_max == Decimal("150000")
    assert job.salary_currency == "USD"
    assert job.posted_at == datetime(2026, 10, 22, 12, 58, 28, tzinfo=timezone.utc)


def test_parse_brazil_only_job_without_salary(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[1]

    assert job.location == "Brazil"
    assert job.accepts_us is False
    assert job.salary_min is None
    assert job.salary_max is None
    assert job.salary_currency == ""