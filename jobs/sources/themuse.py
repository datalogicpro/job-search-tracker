from datetime import datetime

from .base import BaseSource, JobData, location_accepts_us

API_URL = "https://www.themuse.com/api/public/jobs"
REMOTE_LOCATION = "Flexible / Remote"
MAX_PAGES = 5


class TheMuseSource(BaseSource):
    name = "themuse"

    def fetch(self) -> list[JobData]:
        jobs = []
        page = 0
        while page < MAX_PAGES:
            params = {
                "page": page,
                "category": "Software Engineering",
                "level": ["Entry Level", "Internship"],
                "location": REMOTE_LOCATION,
            }
            data = self.request("GET", API_URL, params=params).json()
            jobs.extend(self.parse(item) for item in data.get("results", []))
            page += 1
            if page >= data.get("page_count", 0):
                break
        return jobs

    def parse(self, item: dict) -> JobData:
        location_names = [loc.get("name", "") for loc in item.get("locations") or []]
        other_locations = [name for name in location_names if name != REMOTE_LOCATION]
        levels = [level.get("name", "") for level in item.get("levels") or []]
        published = item.get("publication_date")

        return JobData(
            source=self.name,
            external_id=str(item["id"]),
            title=item.get("name") or "",
            company=(item.get("company") or {}).get("name", ""),
            url=item["refs"]["landing_page"],
            location=", ".join(location_names),
            is_remote=REMOTE_LOCATION in location_names,
            accepts_us=not other_locations or location_accepts_us(", ".join(other_locations)),
            seniority=", ".join(levels),
            description=item.get("contents") or "",
            posted_at=datetime.fromisoformat(published.replace("Z", "+00:00")) if published else None,
        )