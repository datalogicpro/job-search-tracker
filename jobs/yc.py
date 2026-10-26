import logging
import re

import requests

from .sources.base import DEFAULT_TIMEOUT, build_session

logger = logging.getLogger(__name__)

YC_HIRING_URL = "https://yc-oss.github.io/api/companies/hiring.json"
COMPANY_SUFFIX_PATTERN = re.compile(
    r"[,.]?\s+(inc|llc|ltd|corp|co|labs|technologies|ai)\.?$",
    re.IGNORECASE,
)


def normalize_company(name: str) -> str:
    cleaned = name.strip().lower()
    cleaned = COMPANY_SUFFIX_PATTERN.sub("", cleaned)
    return cleaned.strip(" ,.")


def fetch_yc_company_names(session: requests.Session | None = None) -> set[str]:
    session = session or build_session()
    try:
        response = session.get(YC_HIRING_URL, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("YC company list request failed")
        return set()

    companies = response.json()
    names = {normalize_company(company.get("name", "")) for company in companies}
    names.discard("")
    logger.info("YC company list loaded", extra={"count": len(names)})
    return names