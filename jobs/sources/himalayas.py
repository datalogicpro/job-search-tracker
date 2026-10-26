from datetime import datetime, timezone
from decimal import Decimal

from .base import BaseSource, JobData, location_accepts_us

SEARCH_URL = "https://himalayas.app/jobs/api/search"
MAX_PAGES = 5


class HimalayasSource(BaseSource):
    name = "himalayas"

    def fetch(self) -> list[JobData]:
        jobs = []
        for page in range(1, MAX_PAGES + 1):
            params = {
                "q": "python",
                "seniority": "Entry-level",
                "country": "US",
                "sort": "recent",
                "page": page,
            }
            data = self.request("GET", SEARCH_URL, params=params).json()
            items = data.get("jobs", [])
            if not items:
                break
            jobs.extend(self.parse(item) for item in items)
        return jobs

    def parse(self, item: dict) -> JobData:
        restrictions = item.get("locationRestrictions") or []
        names = []
        codes = set()
        for restriction in restrictions:
            if isinstance(restriction, dict):
                names.append(restriction.get("name", ""))
                codes.add(restriction.get("alpha2"))
            else:
                names.append(str(restriction))
        location = ", ".join(name for name in names if name)

        seniority = item.get("seniority") or []
        if isinstance(seniority, str):
            seniority = [seniority]

        is_annual = (item.get("salaryPeriod") or "annual") == "annual"
        salary_min = self.to_decimal(item.get("minSalary")) if is_annual else None
        salary_max = self.to_decimal(item.get("maxSalary")) if is_annual else None
        has_salary = salary_min is not None or salary_max is not None
        published = item.get("pubDate")

        return JobData(
            source=self.name,
            external_id=item["guid"],
            title=item["title"],
            company=item.get("companyName") or "",
            url=item["applicationLink"],
            location=location or "Worldwide",
            is_remote=True,
            accepts_us=not restrictions or "US" in codes or location_accepts_us(location),
            seniority=", ".join(seniority),
            employment_type=item.get("employmentType") or "",
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=(item.get("currency") or "") if has_salary else "",
            description=item.get("description") or "",
            posted_at=datetime.fromtimestamp(published, tz=timezone.utc) if published else None,
        )

    @staticmethod
    def to_decimal(value) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None