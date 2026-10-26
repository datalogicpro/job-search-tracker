from datetime import datetime, timezone

from jobs.filters import is_unpaid, rejection_reason
from jobs.sources.base import JobData


def make_job(**overrides) -> JobData:
    values = {
        "source": "himalayas",
        "external_id": "1",
        "title": "Junior Python Developer",
        "company": "Example Co",
        "url": "https://example.com/job/1",
        "is_remote": True,
        "accepts_us": True,
        "description": "Build APIs with Python and Django.",
    }
    values.update(overrides)
    return JobData(**values)


def test_keeps_junior_python_job():
    assert rejection_reason(make_job()) is None


def test_keeps_developer_title_with_python_in_description():
    job = make_job(title="Backend Engineer Intern")
    assert rejection_reason(job) is None


def test_rejects_job_that_is_not_remote():
    assert rejection_reason(make_job(is_remote=False)) == "not remote"


def test_rejects_job_not_open_to_us():
    assert rejection_reason(make_job(accepts_us=False)) == "not open to US residents"


def test_rejects_closed_job():
    closed = datetime(2026, 10, 1, tzinfo=timezone.utc)
    assert rejection_reason(make_job(closed_at=closed)) == "closed"


def test_rejects_recruiting_agency():
    assert rejection_reason(make_job(is_recruiting_agency=True)) == "recruiting agency"


def test_rejects_blocked_company():
    job = make_job(company="SynergisticIT")
    assert rejection_reason(job) == "blocked company"


def test_rejects_senior_title():
    job = make_job(title="Senior Python Developer")
    assert rejection_reason(job) == "senior title"


def test_rejects_manager_title():
    job = make_job(title="Social Media Manager No Experience Required")
    assert rejection_reason(job) == "senior title"


def test_keeps_junior_to_senior_range_title():
    job = make_job(title="Junior to Senior Fullstack Engineer multiple positions")
    assert rejection_reason(job) is None


def test_keeps_jr_to_sr_range_title():
    job = make_job(title="Jr. to Sr. Python Developer")
    assert rejection_reason(job) is None


def test_rejects_sales_engineer():
    job = make_job(title="Arity - Sales Engineer Intern")
    assert rejection_reason(job) == "not an eligible role"


def test_rejects_military_only_role():
    job = make_job(title="Cybersecurity Intern (TX and AK) - SkillBridge (Military Only)")
    assert rejection_reason(job) == "not an eligible role"


def test_rejects_intern_without_developer_title():
    job = make_job(title="Internship - Data Analyst")
    assert rejection_reason(job) == "not a Python developer job"


def test_rejects_non_developer_job():
    job = make_job(title="Chat Support Agent", description="Answer customer chats.")
    assert rejection_reason(job) == "not a Python developer job"


def test_rejects_developer_title_without_python():
    job = make_job(title="Junior Java Developer", description="Java and Spring.")
    assert rejection_reason(job) == "not a Python developer job"


def test_rejects_bachelors_degree_required():
    job = make_job(description="Python skills. Bachelor's degree in Computer Science required.")
    assert rejection_reason(job) == "degree required"


def test_rejects_degree_with_periods():
    job = make_job(description="Python skills. B.S. in Computer Science.")
    assert rejection_reason(job) == "degree required"


def test_rejects_degree_or_equivalent():
    job = make_job(description="Python skills. BS/BA or equivalent experience.")
    assert rejection_reason(job) == "degree required"


def test_rejects_degree_preferred():
    job = make_job(description="Python skills. Bachelor's degree preferred.")
    assert rejection_reason(job) == "degree required"


def test_rejects_associate_degree():
    job = make_job(description="Python skills. Associate's degree in computer science.")
    assert rejection_reason(job) == "degree required"


def test_rejects_degree_written_in_html():
    job = make_job(description="<ul><li>Python</li><li>Bachelor&#39;s degree</li></ul>")
    assert rejection_reason(job) == "degree required"


def test_keeps_degree_a_plus_when_allowed(settings):
    settings.ALLOW_DEGREE_A_PLUS = True
    job = make_job(description="Python skills. A bachelor's degree is a plus.")
    assert rejection_reason(job) is None


def test_rejects_degree_a_plus_when_not_allowed(settings):
    settings.ALLOW_DEGREE_A_PLUS = False
    job = make_job(description="Python skills. A bachelor's degree is a plus.")
    assert rejection_reason(job) == "degree required"


def test_unpaid_in_title_is_marked_and_kept():
    job = make_job(title="Data Engineer(UNPAID)")
    assert is_unpaid(job) is True
    assert rejection_reason(job) is None


def test_unpaid_internship_is_marked_and_kept():
    job = make_job(title="AI Engineer Internship (UNPAID)")
    assert is_unpaid(job) is True
    assert rejection_reason(job) is None


def test_unpaid_in_description_is_marked():
    job = make_job(description="This is an unpaid role using Python.")
    assert is_unpaid(job) is True


def test_paid_job_is_not_marked_unpaid():
    assert is_unpaid(make_job()) is False