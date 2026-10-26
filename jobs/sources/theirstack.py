import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from django.conf import settings

from .base import BaseSource, JobData, location_accepts_us

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.theirstack.com/v1/jobs/search"


class TheirStackSource(BaseSource):
    name = "theirstack"

    def fetch(self) -> list[JobData]:
        if not settings.THEIRSTACK_API_KEY:
            logger.warning("source skipped, no API key", extra={"source": self.name})
            return []

        headers = {"Authorization": f"Bearer {settings.THEIRSTACK_API_KEY}"}
        body = {
            "posted_at_max_age_days": 7,
            "job_country_code_or": ["US"],
            "job_title_pattern_or": ["junior python", "entry level python", "python intern"],
            "remote": True,
            "company_type": "direct_employer",
            "limit": 10,
        }
        data = self.request("POST", SEARCH_URL, headers=headers, json=body).json()
        return [self.parse(item) for item in data.get("data", [])]

    def parse(self, item: dict) -> JobData:
        location = item.get("location") or ""
        company = item.get("company_object") or {}
        statuses = item.get("employment_statuses") or []

        return JobData(
            source=self.name,
            external_id=str(item["id"]),
            title=item.get("job_title") or "",
            company=item.get("company") or "",
            url=item.get("final_url") or item.get("url") or "",
            location=location or "United States",
            is_remote=bool(item.get("remote")),
            accepts_us=location_accepts_us(location),
            seniority=item.get("seniority") or "",
            employment_type=", ".join(statuses),
            salary_min=self.to_decimal(item.get("min_annual_salary_usd")),
            salary_max=self.to_decimal(item.get("max_annual_salary_usd")),
            salary_currency="USD" if item.get("min_annual_salary_usd") else "",
            description=item.get("description") or "",
            posted_at=self.to_datetime(item.get("date_posted")),
            is_recruiting_agency=bool(company.get("is_recruiting_agency")),
            closed_at=self.parse_closed(item.get("closed_at")),
        )

    @staticmethod
    def to_decimal(value) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None

    @staticmethod
    def to_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        day = date.fromisoformat(value)
        return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)

    @staticmethod
    def parse_closed(value: str | None) -> datetime | None:
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None