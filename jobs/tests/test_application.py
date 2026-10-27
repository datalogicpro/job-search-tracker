from io import StringIO

import pytest
from django.core import mail, signing
from django.core.management import call_command
from django.db.models import ProtectedError

from jobs import applications
from jobs.applications import make_token, mark_applied_url, read_token
from jobs.models import Application, Job

SITE_URL = "https://tracker.example.com"


def make_job(external_id: str = "1", **overrides) -> Job:
    values = {
        "source": "jobicy",
        "external_id": external_id,
        "title": f"Junior Python Developer {external_id}",
        "company": "Example Co",
        "url": f"https://jobicy.com/jobs/{external_id}",
    }
    values.update(overrides)
    return Job.objects.create(**values)


def mark_path(job: Job) -> str:
    return f"/applications/mark/{make_token(job.pk)}/"


def test_token_reads_back_to_same_job():
    assert read_token(make_token(42)) == 42


def test_changed_token_is_refused():
    with pytest.raises(signing.BadSignature):
        read_token(make_token(42) + "x")


@pytest.mark.django_db
def test_mark_applied_url_uses_site_url(settings):
    settings.SITE_URL = SITE_URL + "/"
    job = make_job()

    assert mark_applied_url(job).startswith(f"{SITE_URL}/applications/mark/")


@pytest.mark.django_db
def test_opening_link_only_shows_button(client):
    job = make_job()

    response = client.get(mark_path(job))

    assert response.status_code == 200
    assert b"Mark as applied" in response.content
    assert not Application.objects.exists()


@pytest.mark.django_db
def test_clicking_button_marks_job_applied_once(client):
    job = make_job()

    client.post(mark_path(job))
    response = client.post(mark_path(job))

    assert response.status_code == 200
    assert b"Marked as applied" in response.content
    assert Application.objects.filter(job=job).count() == 1
    assert Application.objects.get(job=job).status == Application.Status.APPLIED


@pytest.mark.django_db
def test_bad_link_shows_error(client):
    response = client.get("/applications/mark/not-a-real-token/")

    assert response.status_code == 400
    assert b"This link is not valid." in response.content


@pytest.mark.django_db
def test_expired_link_shows_error(client, monkeypatch):
    job = make_job()
    monkeypatch.setattr(applications, "LINK_MAX_AGE_SECONDS", -1)

    response = client.get(mark_path(job))

    assert response.status_code == 400
    assert b"This link has expired." in response.content


@pytest.mark.django_db
def test_applied_filter_on_job_list(client):
    applied_job = make_job("1")
    make_job("2")
    Application.objects.create(job=applied_job)

    applied = client.get("/api/jobs/?applied=true").json()["results"]
    not_applied = client.get("/api/jobs/?applied=false").json()["results"]

    assert [job["title"] for job in applied] == ["Junior Python Developer 1"]
    assert [job["title"] for job in not_applied] == ["Junior Python Developer 2"]


@pytest.mark.django_db
def test_job_with_application_cannot_be_deleted():
    job = make_job()
    Application.objects.create(job=job)

    with pytest.raises(ProtectedError):
        job.delete()


@pytest.mark.django_db
def test_digest_includes_mark_applied_link(settings):
    settings.SITE_URL = SITE_URL
    settings.DIGEST_TO = "digest@example.com"
    settings.DEFAULT_FROM_EMAIL = "sender@example.com"
    make_job()

    call_command("send_digest", stdout=StringIO())

    assert f"Mark as applied: {SITE_URL}/applications/mark/" in mail.outbox[0].body