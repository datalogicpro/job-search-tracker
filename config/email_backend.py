from email.utils import make_msgid

from django.core.mail.backends.smtp import EmailBackend


class FixedHostnameEmailBackend(EmailBackend):
    """SMTP backend that never sends the computer's name.

    Django's SMTP backend uses the computer's name when it greets the mail
    server, and EmailMessage.message() uses it to build each Message-ID.
    This backend uses the local_hostname option for both instead.
    """

    def __init__(self, *, local_hostname, **kwargs):
        super().__init__(**kwargs)
        self.local_hostname = local_hostname

    @property
    def connection_class(self):
        base_class = super().connection_class
        local_hostname = self.local_hostname

        def connect(host, port, **kwargs):
            kwargs["local_hostname"] = local_hostname
            return base_class(host, port, **kwargs)

        return connect

    def send_messages(self, email_messages):
        for message in email_messages:
            header_names = {name.lower() for name in message.extra_headers}
            if "message-id" not in header_names:
                message.extra_headers["Message-ID"] = make_msgid(domain=self.local_hostname)
        return super().send_messages(email_messages)