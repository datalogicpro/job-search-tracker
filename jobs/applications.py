from django.conf import settings
from django.core import signing
from django.urls import reverse

from .models import Job

MARK_APPLIED_SALT = "jobs.mark-applied"
LINK_MAX_AGE_SECONDS = 60 * 60 * 24 * 30


def make_token(job_id: int) -> str:
    return signing.dumps(job_id, salt=MARK_APPLIED_SALT)


def read_token(token: str) -> int:
    """Return the job ID in a token.

    Raises signing.SignatureExpired when the link is older than 30 days,
    and signing.BadSignature when the token was not made by this app.
    """
    return signing.loads(token, salt=MARK_APPLIED_SALT, max_age=LINK_MAX_AGE_SECONDS)


def mark_applied_url(job: Job) -> str:
    path = reverse("mark-applied", args=[make_token(job.pk)])
    return f"{settings.SITE_URL.rstrip('/')}{path}"