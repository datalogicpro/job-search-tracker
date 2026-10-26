import json
from datetime import datetime, timezone
from pathlib import Path

from jobs.sources.themuse import TheMuseSource

FIXTURE = Path(__file__).parent / "fixtures" / "themuse.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fetch_with_fixture(monkeypatch, calls=None):
    source = TheMuseSource()

    def fake_request(method, url, **kwargs):
        if calls is not None:
            calls.append(kwargs["params"]["page"])
        return FakeResponse(load_fixture())

    monkeypatch.setattr(source, "request", fake_request)
    return source.fetch()


def test_fetch_stops_after_last_page(monkeypatch):
    calls = []
    jobs = fetch_with_fixture(monkeypatch, calls)

    assert calls == [0]
    assert [job.external_id for job in jobs] == ["22018131", "20839023", "22018200"]


def test_parse_remote_job_limited_to_mexico(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[0]

    assert job.source == "themuse"
    assert job.title == "Junior Platform Support Engineer"
    assert job.company == "Summitcore"
    assert job.url == "https://www.themuse.com/jobs/summitcore/junior-platform-support-engineer"
    assert job.location == "Flexible / Remote, Mexico City, Mexico"
    assert job.is_remote is True
    assert job.accepts_us is False
    assert job.seniority == "Entry Level"
    assert job.posted_at == datetime(2026, 8, 1, 18, 48, 50, tzinfo=timezone.utc)


def test_parse_remote_only_job(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[1]

    assert job.location == "Flexible / Remote"
    assert job.is_remote is True
    assert job.accepts_us is True
    assert job.seniority == "Entry Level, Internship"


def test_parse_remote_job_with_us_city(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[2]

    assert job.location == "Flexible / Remote, Los Angeles, CA"
    assert job.accepts_us is True