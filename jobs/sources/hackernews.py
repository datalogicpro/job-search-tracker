import html
import re
from datetime import datetime

from .base import BaseSource, JobData, location_accepts_us

SEARCH_BY_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"
ITEM_URL = "https://news.ycombinator.com/item?id={}"
HIRING_TITLE = "who is hiring?"
PYTHON_PATTERN = re.compile(r"\bpython\b", re.IGNORECASE)
REMOTE_PATTERN = re.compile(r"\bremote\b", re.IGNORECASE)
REMOTE_REGION_PATTERN = re.compile(r"\bremote\b\s*\(([^)]*)\)", re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")
ROLE_PATTERN = re.compile(
    r"\b(engineers?|engineering|developers?|programmers?|swes?)\b", re.IGNORECASE
)
URL_PATTERN = re.compile(r"^(https?://|www\.)", re.IGNORECASE)


class HackerNewsSource(BaseSource):
    name = "hackernews"

    def fetch(self) -> list[JobData]:
        story_id = self.find_hiring_story_id()
        if story_id is None:
            return []

        params = {"tags": f"comment,story_{story_id}", "hitsPerPage": 1000}
        data = self.request("GET", SEARCH_BY_DATE_URL, params=params).json()

        jobs = []
        for hit in data.get("hits", []):
            if str(hit.get("parent_id")) != str(story_id):
                continue
            text = self.clean_text(hit.get("comment_text") or "")
            if PYTHON_PATTERN.search(text) and REMOTE_PATTERN.search(text):
                jobs.append(self.parse(hit, text))
        return jobs

    def find_hiring_story_id(self) -> int | None:
        params = {"tags": "story,author_whoishiring", "hitsPerPage": 5}
        data = self.request("GET", SEARCH_BY_DATE_URL, params=params).json()
        for hit in data.get("hits", []):
            if HIRING_TITLE in (hit.get("title") or "").lower():
                return int(hit["objectID"])
        return None

    @staticmethod
    def clean_text(raw: str) -> str:
        with_breaks = raw.replace("<p>", "\n")
        return html.unescape(TAG_PATTERN.sub("", with_breaks)).strip()

    @staticmethod
    def pick_title(parts: list[str], first_line: str) -> str:
        for part in parts[1:]:
            if not URL_PATTERN.match(part) and ROLE_PATTERN.search(part):
                return part
        return parts[1] if len(parts) > 1 else first_line

    def parse(self, hit: dict, text: str) -> JobData:
        first_line = text.split("\n", 1)[0]
        parts = [part.strip() for part in first_line.split("|")]
        company = parts[0] if parts else ""
        title = self.pick_title(parts, first_line)

        region_match = REMOTE_REGION_PATTERN.search(first_line)
        accepts_us = location_accepts_us(region_match.group(1)) if region_match else True
        created = hit.get("created_at")

        return JobData(
            source=self.name,
            external_id=str(hit["objectID"]),
            title=title[:300],
            company=company[:300],
            url=ITEM_URL.format(hit["objectID"]),
            location=first_line[:300],
            is_remote=True,
            accepts_us=accepts_us,
            description=text,
            posted_at=datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None,
        )