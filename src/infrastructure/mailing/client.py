from functools import lru_cache

import aiosmtplib
from email.message import EmailMessage

from core.config import get_settings
from core.config.mailing import MailingSettings
from core.utils.retry import retry

settings = get_settings()


class SMTPMailClient:

    def __init__(self, mailing_config: MailingSettings):
        if mailing_config is None:
            raise ValueError("Mailing configuration is not provided.")

        if mailing_config.smtp_host is None:
            raise ValueError("SMTP host is not configured.")

        if mailing_config.smtp_port is None:
            raise ValueError("SMTP port is not configured.")

        self.config = mailing_config

    @retry(max_attempts=3)
    async def send(self, message: EmailMessage) -> None:
        kwargs = {
            "hostname": self.config.smtp_host,
            "port": self.config.smtp_port,
        }

        if self.config.smtp_username and self.config.smtp_password:
            kwargs["username"] = self.config.smtp_username
            kwargs["password"] = self.config.smtp_password.get_secret_value()
            kwargs["start_tls"] = self.config.smtp_use_tls

        await aiosmtplib.send(message, **kwargs)


@lru_cache
def get_mail_client():
    return SMTPMailClient(settings.mailing)
