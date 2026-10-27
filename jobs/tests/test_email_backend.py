from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend

from config.email_backend import FixedHostnameEmailBackend

FIXED_NAME = "job-search-tracker"


class FakeSMTP:
    def __init__(self, host, port, **kwargs):
        self.host = host
        self.port = port
        self.kwargs = kwargs


def make_backend() -> FixedHostnameEmailBackend:
    return FixedHostnameEmailBackend(
        alias="test",
        host="smtp.example.com",
        use_tls=True,
        local_hostname=FIXED_NAME,
    )


def make_message(**kwargs) -> EmailMessage:
    return EmailMessage("Subject", "Body", "sender@example.com", ["to@example.com"], **kwargs)


def test_greeting_uses_fixed_name(monkeypatch):
    monkeypatch.setattr("smtplib.SMTP", FakeSMTP)
    backend = make_backend()

    connection = backend.connection_class("smtp.example.com", 587, local_hostname="MY-PC", timeout=15)

    assert connection.kwargs["local_hostname"] == FIXED_NAME
    assert connection.kwargs["timeout"] == 15


def test_message_id_uses_fixed_name(monkeypatch):
    monkeypatch.setattr(EmailBackend, "send_messages", lambda self, messages: len(messages))
    message = make_message()

    sent = make_backend().send_messages([message])

    assert sent == 1
    assert message.message()["Message-ID"].endswith(f"@{FIXED_NAME}>")


def test_existing_message_id_is_kept(monkeypatch):
    monkeypatch.setattr(EmailBackend, "send_messages", lambda self, messages: len(messages))
    message = make_message(headers={"Message-ID": "<given@example.com>"})

    make_backend().send_messages([message])

    assert message.message()["Message-ID"] == "<given@example.com>"