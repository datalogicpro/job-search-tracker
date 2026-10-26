import logging
from datetime import datetime
from decimal import Decimal

from django.conf import settings

from .base import BaseSource, JobData, location_accepts_us

logger = logging.getLogger(__name__)

SEARCH_URL = "https://jsearch.p.rapidapi.com/search-v2"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"


class JSearchSource(BaseSource):
    name = "jsearch"

    def fetch(self) -> list[JobData]:
        if not settings.RAPIDAPI_KEY:
            logger.warning("source skipped, no API key", extra={"source": self.name})
            return []

        headers = {
            "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
        }
        params = {
            "query": "python developer",
            "country": "us",
            "date_posted": "month",
            "work_from_home": "true",
            "job_requirements": "no_experience,under_3_years_experience",
            "num_pages": 1,
        }
        data = self.request("GET", SEARCH_URL, headers=headers, params=params).json()
        items = (data.get("data") or {}).get("jobs", [])
        return [self.parse(item) for item in items]

    def parse(self, item: dict) -> JobData:
        location = item.get("job_location") or ""
        is_yearly = item.get("job_salary_period") == "YEAR"
        posted = item.get("job_posted_at_datetime_utc")

        return JobData(
            source=self.name,
            external_id=item.get("job_uid") or item["job_id"],
            title=item.get("job_title") or "",
            company=item.get("employer_name") or "",
            url=item.get("job_apply_link") or "",
            location=location,
            is_remote=bool(item.get("job_is_remote")),
            accepts_us=location_accepts_us(location),
            employment_type=item.get("job_employment_type") or "",
            salary_min=self.to_decimal(item.get("job_min_salary")) if is_yearly else None,
            salary_max=self.to_decimal(item.get("job_max_salary")) if is_yearly else None,
            salary_currency="USD" if is_yearly and item.get("job_min_salary") else "",
            description=item.get("job_description") or "",
            posted_at=datetime.fromisoformat(posted.replace("Z", "+00:00")) if posted else None,
        )

    @staticmethod
    def to_decimal(value) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None
    