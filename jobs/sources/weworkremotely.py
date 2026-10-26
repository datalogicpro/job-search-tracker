import re
from email.utils import parsedate_to_datetime

from defusedxml import ElementTree

from .base import BaseSource, JobData, location_accepts_us

FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
PYTHON_PATTERN = re.compile(r"\bpython\b", re.IGNORECASE)


class WeWorkRemotelySource(BaseSource):
    name = "weworkremotely"

    def fetch(self) -> list[JobData]:
        response = self.request("GET", FEED_URL)
        root = ElementTree.fromstring(response.content)
        jobs = []
        for item in root.iter("item"):
            job = self.parse(item)
            if PYTHON_PATTERN.search(job.title) or PYTHON_PATTERN.search(job.description):
                jobs.append(job)
        return jobs

    def parse(self, item) -> JobData:
        raw_title = item.findtext("title", default="")
        company, _, title = raw_title.partition(": ")
        if not title:
            company, title = "", raw_title
        region = item.findtext("region", default="")
        published = item.findtext("pubDate")

        return JobData(
            source=self.name,
            external_id=item.findtext("guid", default=""),
            title=title.strip(),
            company=company.strip(),
            url=item.findtext("link", default=""),
            location=region,
            is_remote=True,
            accepts_us=location_accepts_us(region),
            employment_type=item.findtext("type", default=""),
            description=item.findtext("description", default=""),
            posted_at=parsedate_to_datetime(published) if published else None,
        )