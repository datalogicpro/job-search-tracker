import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
USER_AGENT = "job-search-tracker/0.1 (+https://github.com/datalogicpro)"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_names(filename: str) -> tuple[str, ...]:
    lines = (DATA_DIR / filename).read_text(encoding="utf-8").splitlines()
    return tuple(line.strip() for line in lines if line.strip() and not line.startswith("#"))


NO_LIMIT_LOCATIONS = frozenset({"remote"})
US_LOCATION_TERMS = (
    "us",
    "usa",
    "u.s.",
    "united states",
    "north america",
    "americas",
    "worldwide",
    "global",
    "anywhere",
    "washington dc",
    "washington, dc",
    "district of columbia",
)
US_STATES = (
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
)
US_STATE_CODES = (
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
)
US_CITIES = load_names("us_cities.txt")
AMBIGUOUS_US_CITIES = load_names("us_cities_ambiguous.txt")


def names_pattern(names: tuple[str, ...]) -> str:
    return "|".join(re.escape(name) for name in names)


US_LOCATION_PATTERN = re.compile(
    r"(?<!\w)(" + names_pattern(US_LOCATION_TERMS + US_STATES + US_CITIES) + r")(?!\w)",
    re.IGNORECASE,
)
AMBIGUOUS_CITY_PATTERN = re.compile(
    r"(?<!\w)(?i:" + names_pattern(AMBIGUOUS_US_CITIES) + r")\s*,\s*("
    + names_pattern(US_STATE_CODES) + r")(?!\w)"
)


@dataclass
class JobData:
    source: str
    external_id: str
    title: str
    company: str
    url: str
    location: str = ""
    is_remote: bool = False
    accepts_us: bool = False
    seniority: str = ""
    employment_type: str = ""
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str = ""
    description: str = ""
    posted_at: datetime | None = None
    is_recruiting_agency: bool = False
    closed_at: datetime | None = None


def location_accepts_us(location: str | None) -> bool:
    text = (location or "").strip()
    if not text or text.casefold() in NO_LIMIT_LOCATIONS:
        return True
    return bool(US_LOCATION_PATTERN.search(text) or AMBIGUOUS_CITY_PATTERN.search(text))


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


class BaseSource(ABC):
    name: str = ""

    def __init__(self, session: requests.Session | None = None):
        self.session = session or build_session()

    @abstractmethod
    def fetch(self) -> list[JobData]:
        ...

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        start = time.monotonic()
        try:
            response = self.session.request(method, url, **kwargs)
        except requests.RequestException:
            logger.exception(
                "source request failed",
                extra={"source": self.name, "url": url},
            )
            raise
        duration_ms = round((time.monotonic() - start) * 1000)
        logger.info(
            "source request finished",
            extra={
                "source": self.name,
                "url": url,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.raise_for_status()
        return response