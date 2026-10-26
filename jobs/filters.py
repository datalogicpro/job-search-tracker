import html
import re

from django.conf import settings

from .sources.base import JobData

BLOCKED_COMPANIES = (
    "synergisticit",
    "hirefinity",
    "remote quest jobs",
)

SENIOR_TITLE_PATTERN = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|manager|director|head of|architect)\b",
    re.IGNORECASE,
)
JUNIOR_TITLE_PATTERN = re.compile(
    r"\b(junior|jr\.?|entry|entry-level)\b",
    re.IGNORECASE,
)
INELIGIBLE_TITLE_PATTERN = re.compile(
    r"\b(sales|presales|pre-sales|military only|skillbridge)\b",
    re.IGNORECASE,
)
DEVELOPER_TITLE_PATTERN = re.compile(
    r"\b(developer|engineer|engineering|programmer|software|backend|back-end)\b",
    re.IGNORECASE,
)
PYTHON_PATTERN = re.compile(r"\bpython\b", re.IGNORECASE)
UNPAID_PATTERN = re.compile(r"\bunpaid\b", re.IGNORECASE)

DEGREE_PATTERN = re.compile(
    r"\b(bachelor'?s?|b\.s\.|b\.a\.|bs/ba|ba/bs|undergraduate degree|"
    r"associate'?s? degree|a\.s\. degree|master'?s? degree|ph\.?d|"
    r"degree in (computer science|computer engineering|engineering|"
    r"information technology|software|mathematics|a related field))(?!\w)",
    re.IGNORECASE,
)
DEGREE_EXCEPTION_PATTERN = re.compile(r"a plus|nice to have", re.IGNORECASE)
TAG_PATTERN = re.compile(r"<[^>]+>")
DEGREE_CONTEXT_BEFORE = 100
DEGREE_CONTEXT_AFTER = 150


def plain_text(raw: str) -> str:
    return html.unescape(TAG_PATTERN.sub(" ", raw or ""))


def requires_degree(job: JobData) -> bool:
    text = plain_text(job.description)
    for match in DEGREE_PATTERN.finditer(text):
        if not settings.ALLOW_DEGREE_A_PLUS:
            return True
        start = max(0, match.start() - DEGREE_CONTEXT_BEFORE)
        end = match.end() + DEGREE_CONTEXT_AFTER
        if not DEGREE_EXCEPTION_PATTERN.search(text[start:end]):
            return True
    return False


def is_senior_only_title(title: str) -> bool:
    return bool(SENIOR_TITLE_PATTERN.search(title) and not JUNIOR_TITLE_PATTERN.search(title))


def rejection_reason(job: JobData) -> str | None:
    if not job.is_remote:
        return "not remote"
    if not job.accepts_us:
        return "not open to US residents"
    if job.closed_at is not None:
        return "closed"
    if job.is_recruiting_agency:
        return "recruiting agency"

    company = job.company.lower()
    if any(blocked in company for blocked in BLOCKED_COMPANIES):
        return "blocked company"

    if is_senior_only_title(job.title):
        return "senior title"
    if INELIGIBLE_TITLE_PATTERN.search(job.title):
        return "not an eligible role"

    is_python_job = PYTHON_PATTERN.search(job.title) or (
        DEVELOPER_TITLE_PATTERN.search(job.title) and PYTHON_PATTERN.search(job.description)
    )
    if not is_python_job:
        return "not a Python developer job"

    if requires_degree(job):
        return "degree required"
    return None


def is_unpaid(job: JobData) -> bool:
    return bool(UNPAID_PATTERN.search(job.title) or UNPAID_PATTERN.search(job.description))