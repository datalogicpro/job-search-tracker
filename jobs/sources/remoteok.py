from datetime import datetime
from decimal import Decimal

from .base import BaseSource, JobData, location_accepts_us

API_URL = "https://remoteok.com/api"


class RemoteOKSource(BaseSource):
    name = "remoteok"

    def fetch(self) -> list[JobData]:
        items = self.request("GET", API_URL).json()
        jobs = []
        for item in items:
            if "id" not in item:
                continue
            if not self.is_python_job(item):
                continue
            jobs.append(self.parse(item))
        return jobs

    @staticmethod
    def is_python_job(item: dict) -> bool:
        tags = [tag.lower() for tag in item.get("tags") or []]
        title = (item.get("position") or "").lower()
        return "python" in tags or "python" in title

    def parse(self, item: dict) -> JobData:
        location = item.get("location") or ""
        posted = item.get("date")

        return JobData(
            source=self.name,
            external_id=str(item["id"]),
            title=item.get("position") or "",
            company=item.get("company") or "",
            url=item["url"],
            location=location or "Worldwide",
            is_remote=True,
            accepts_us=location_accepts_us(location),
            salary_min=self.to_salary(item.get("salary_min")),
            salary_max=self.to_salary(item.get("salary_max")),
            salary_currency="USD" if item.get("salary_min") else "",
            description=item.get("description") or "",
            posted_at=datetime.fromisoformat(posted) if posted else None,
        )

    @staticmethod
    def to_salary(value) -> Decimal | None:
        return Decimal(str(value)) if value else None