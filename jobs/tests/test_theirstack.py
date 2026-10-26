import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from jobs.sources.theirstack import TheirStackSource

FIXTURE = Path(__file__).parent / "fixtures" / "theirstack.json"
TEST_KEY = "test-key"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fetch_with_fixture(monkeypatch, settings, calls=None):
    settings.THEIRSTACK_API_KEY = TEST_KEY
    source = TheirStackSource()

    def fake_request(method, url, **kwargs):
        if calls is not None:
            calls.append((method, kwargs["headers"], kwargs["json"]))
        return FakeResponse(load_fixture())

    monkeypatch.setattr(source, "request", fake_request)
    return source.fetch()


def test_fetch_skips_without_key(monkeypatch, settings):
    settings.THEIRSTACK_API_KEY = ""
    source = TheirStackSource()
    calls = []
    monkeypatch.setattr(source, "request", lambda *args, **kwargs: calls.append(args))

    assert source.fetch() == []
    assert calls == []


def test_fetch_sends_bearer_token_and_us_remote_body(monkeypatch, settings):
    calls = []
    fetch_with_fixture(monkeypatch, settings, calls)

    method, headers, body = calls[0]
    assert method == "POST"
    assert headers == {"Authorization": f"Bearer {TEST_KEY}"}
    assert body["job_country_code_or"] == ["US"]
    assert body["remote"] is True
    assert body["company_type"] == "direct_employer"


def test_parse_direct_employer_job(monkeypatch, settings):
    job = fetch_with_fixture(monkeypatch, settings)[0]

    assert job.source == "theirstack"
    assert job.external_id == "900000001"
    assert job.title == "Junior Python Developer"
    assert job.company == "Saltmarsh Systems"
    assert job.url == "https://careers.saltmarsh.example/jobs/junior-python-developer"
    assert job.location == "United States"
    assert job.is_remote is True
    assert job.accepts_us is True
    assert job.seniority == "junior"
    assert job.employment_type == "full_time"
    assert job.salary_min == Decimal("70000")
    assert job.salary_max == Decimal("90000")
    assert job.salary_currency == "USD"
    assert job.posted_at == datetime(2026, 10, 20, tzinfo=timezone.utc)
    assert job.is_recruiting_agency is False
    assert job.closed_at is None


def test_parse_closed_agency_job(monkeypatch, settings):
    job = fetch_with_fixture(monkeypatch, settings)[1]

    assert job.url == "https://www.linkedin.com/jobs/view/900000002/"
    assert job.location == "Latin America"
    assert job.accepts_us is False
    assert job.employment_type == "full_time, contract"
    assert job.salary_min is None
    assert job.salary_currency == ""
    assert job.is_recruiting_agency is True
    assert job.closed_at == datetime(2026, 10, 7, 12, 12, 47, tzinfo=timezone.utc)