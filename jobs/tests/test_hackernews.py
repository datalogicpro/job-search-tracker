import json
from datetime import datetime, timezone
from pathlib import Path

from jobs.sources.hackernews import HackerNewsSource

FIXTURE = Path(__file__).parent / "fixtures" / "hackernews.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fetch_with_fixture(monkeypatch, calls=None):
    source = HackerNewsSource()
    fixture = load_fixture()

    def fake_request(method, url, **kwargs):
        tags = kwargs["params"]["tags"]
        if calls is not None:
            calls.append(tags)
        key = "stories" if tags.startswith("story,") else "comments"
        return FakeResponse(fixture[key])

    monkeypatch.setattr(source, "request", fake_request)
    return source.fetch()


def test_fetch_uses_who_is_hiring_story(monkeypatch):
    calls = []
    fetch_with_fixture(monkeypatch, calls)

    assert calls == ["story,author_whoishiring", "comment,story_49922569"]


def test_fetch_skips_replies_and_non_python_posts(monkeypatch):
    jobs = fetch_with_fixture(monkeypatch)
    assert [job.external_id for job in jobs] == ["50095249", "49925489", "49961551", "49924974"]


def test_parse_title_after_link_and_location(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[0]

    assert job.source == "hackernews"
    assert job.company == "Harborlight"
    assert job.title == "Software Engineer"
    assert job.url == "https://news.ycombinator.com/item?id=50095249"
    assert job.location == (
        "Harborlight | https://harborlight.example | REMOTE (US or Canada) | "
        "Software Engineer | Full-Time"
    )
    assert job.is_remote is True
    assert job.accepts_us is True
    assert "Python and Django" in job.description
    assert job.posted_at == datetime(2026, 10, 14, 21, 5, 6, tzinfo=timezone.utc)


def test_parse_remote_global_job(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[1]

    assert job.company == "Fieldnote (YC S18)"
    assert job.title == "Backend Software Engineer"
    assert job.accepts_us is True


def test_parse_uk_only_job(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[2]

    assert job.title == "AI Engineer"
    assert job.accepts_us is False


def test_parse_post_without_title_falls_back_to_second_part(monkeypatch):
    job = fetch_with_fixture(monkeypatch)[3]

    assert job.company == "Quillworks"
    assert job.title == "Remote (US)"
    assert job.accepts_us is True