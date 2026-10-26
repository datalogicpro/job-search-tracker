import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from jobs.sources.jsearch import JSearchSource

FIXTURE = Path(__file__).parent / "fixtures" / "jsearch.json"
TEST_KEY = "test-key"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fetch_with_fixture(monkeypatch, settings, calls=None):
    settings.RAPIDAPI_KEY = TEST_KEY
    source = JSearchSource()

    def fake_request(method, url, **kwargs):
        if calls is not None:
            calls.append(kwargs["headers"])
        return FakeResponse(load_fixture())

    monkeypatch.setattr(source, "request", fake_request)
    return source.fetch()


def test_fetch_skips_without_key(monkeypatch, settings):
    settings.RAPIDAPI_KEY = ""
    source = JSearchSource()
    calls = []
    monkeypatch.setattr(source, "request", lambda *args, **kwargs: calls.append(args))

    assert source.fetch() == []
    assert calls == []


def test_fetch_sends_rapidapi_headers(monkeypatch, settings):
    calls = []
    fetch_with_fixture(monkeypatch, settings, calls)

    assert calls == [{"X-RapidAPI-Key": TEST_KEY, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}]


def test_parse_job_with_yearly_salary(monkeypatch, settings):
    job = fetch_with_fixture(monkeypatch, settings)[0]

    assert job.source == "jsearch"
    assert job.external_id == "av60YOYefK2hzUEbAAAAAA=="
    assert job.title == "Junior Python Developer"
    assert job.company == "Bluefin Analytics"
    assert job.url == "https://careers.bluefin.example/jobs/junior-python-developer"
    assert job.location == "Anywhere"
    assert job.is_remote is True
    assert job.accepts_us is True
    assert job.employment_type == "Full-time"
    assert job.salary_min == Decimal("60000")
    assert job.salary_max == Decimal("80000")
    assert job.salary_currency == "USD"
    assert job.posted_at == datetime(2026, 10, 22, tzinfo=timezone.utc)


def test_parse_hourly_salary_is_not_saved(monkeypatch, settings):
    job = fetch_with_fixture(monkeypatch, settings)[1]

    assert job.salary_min is None
    assert job.salary_max is None
    assert job.salary_currency == ""


def test_parse_job_without_uid_uses_job_id(monkeypatch, settings):
    job = fetch_with_fixture(monkeypatch, settings)[2]

    assert job.external_id == "LONGJOBID3LONGJOBID3LONGJOBID3"
    assert job.location == "Toronto, ON, Canada"
    assert job.accepts_us is False