import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from jobs.sources.himalayas import HimalayasSource

FIXTURE = Path(__file__).parent / "fixtures" / "himalayas.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data: dict):
        self.data = data

    def json(self) -> dict:
        return self.data


def test_parse_us_job():
    item = load_fixture()["jobs"][0]
    job = HimalayasSource().parse(item)

    assert job.source == "himalayas"
    assert job.external_id == item["guid"]
    assert job.title == "Internship - Research Engineer"
    assert job.company == "Smule,Inc."
    assert job.url == item["applicationLink"]
    assert job.seniority == "Entry-level"
    assert job.location == "United States"
    assert job.is_remote is True
    assert job.accepts_us is True
    assert job.salary_min is None
    assert job.posted_at == datetime.fromtimestamp(1792857397, tz=timezone.utc)


def test_parse_canada_only_job():
    item = load_fixture()["jobs"][1]
    job = HimalayasSource().parse(item)

    assert job.location == "Canada"
    assert job.accepts_us is False
    assert job.salary_min == Decimal("85000")
    assert job.salary_max == Decimal("105000")
    assert job.salary_currency == "CAD"


def test_fetch_stops_on_empty_page(monkeypatch):
    pages = [load_fixture(), {"jobs": []}]
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append(kwargs["params"]["page"])
        return FakeResponse(pages.pop(0))

    source = HimalayasSource()
    monkeypatch.setattr(source, "request", fake_request)

    jobs = source.fetch()

    assert len(jobs) == 2
    assert calls == [1, 2]