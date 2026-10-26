from datetime import datetime
from decimal import Decimal

from .base import BaseSource, JobData, location_accepts_us

API_URL = "https://jobicy.com/api/v2/remote-jobs"
ANNUAL_PERIOD = "yearly"


class JobicySource(BaseSource):
    name = "jobicy"

    def fetch(self) -> list[JobData]:
        params = {"count": 50, "tag": "python"}
        data = self.request("GET", API_URL, params=params).json()
        return [self.parse(item) for item in data.get("jobs", [])]

    def parse(self, item: dict) -> JobData:
        geo = item.get("jobGeo") or ""
        job_types = item.get("jobType") or []
        if isinstance(job_types, str):
            job_types = [job_types]
        published = item.get("pubDate")

        salary_min = salary_max = None
        if item.get("salaryPeriod") == ANNUAL_PERIOD:
            salary_min = self.to_decimal(item.get("salaryMin"))
            salary_max = self.to_decimal(item.get("salaryMax"))
        has_salary = salary_min is not None or salary_max is not None

        return JobData(
            source=self.name,
            external_id=str(item["id"]),
            title=item.get("jobTitle") or "",
            company=item.get("companyName") or "",
            url=item["url"],
            location=geo,
            is_remote=True,
            accepts_us=location_accepts_us(geo),
            seniority=item.get("jobLevel") or "",
            employment_type=", ".join(job_types),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=(item.get("salaryCurrency") or "") if has_salary else "",
            description=item.get("jobDescription") or "",
            posted_at=datetime.fromisoformat(published) if published else None,
        )

    @staticmethod
    def to_decimal(value) -> Decimal | None:
        return Decimal(str(value)) if value not in (None, "") else None