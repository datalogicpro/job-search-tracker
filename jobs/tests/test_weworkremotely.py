from datetime import datetime, timezone
from pathlib import Path

from jobs.sources.weworkremotely import WeWorkRemotelySource

FIXTURE = Path(__file__).parent / "fixtures" / "weworkremotely.xml"
JOB_URL = "https://weworkremotely.com/remote-jobs/"


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content


def fetch_with_fixture(monkeypatch):
    source = WeWorkRemotelySource()
    monkeypatch.setattr(
        source, "request", lambda method, url, **kwargs: FakeResponse(FIXTURE.read_bytes())
    )
    return source.fetch()


def test_fetch_skips_non_python_jobs(monkeypatch):
    jobs = fetch_with_fixture(monkeypatch)
    assert [job.external_id for job in jobs] == [
        JOB_URL + "northwind-labs-junior-python-developer",
        JOB_URL + "brightline-studio-python-backend-engineer",
        JOB_URL + "python-automation-engineer",
    ]


def test_parse_worldwide_job(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[0]

    assert job.source == "weworkremotely"
    assert job.title == "Junior Python Developer"
    assert job.company == "Northwind Labs"
    assert job.url == JOB_URL + "northwind-labs-junior-python-developer"
    assert job.location == "Anywhere in the World"
    assert job.is_remote is True
    assert job.accepts_us is True
    assert job.employment_type == ""
    assert "Build REST APIs with Python and Django." in job.description
    assert job.posted_at == datetime(2026, 10, 20, 16, 5, 12, tzinfo=timezone.utc)


def test_parse_europe_only_job(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[1]

    assert job.location == "Europe Only"
    assert job.accepts_us is False


def test_parse_title_without_company(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[2]

    assert job.company == ""
    assert job.title == "Python Automation Engineer"
    assert job.accepts_us is True