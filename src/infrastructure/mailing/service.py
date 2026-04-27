from email.message import EmailMessage
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from infrastructure.mailing.client import SMTPMailClient, get_mail_client

BASE_DIR = Path(__file__).resolve().parent


class MailService:
    def __init__(self, client: SMTPMailClient) -> None:
        self.client = client

        if self.client is None:
            raise AttributeError("SMTPMailClient not set")

        self.sender = client.config.smtp_admin

        if self.sender is None:
            raise AttributeError("Sender not set")

        self.templates_dir = Path(BASE_DIR / "templates")

        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml"), default=False
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _render_html(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(f"{template_name}.html")
        return template.render(**kwargs).strip()

    def _render_text(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(f"{template_name}.txt")
        return template.render(**kwargs).strip()

    def build_message(
        self,
        recipient: str,
        subject: str,
        template_name: str,
        **kwargs,
    ) -> EmailMessage:
        html_content = self._render_html(template_name, **kwargs)
        plain_content = self._render_text(template_name, **kwargs)

        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = subject

        message.set_content(plain_content)
        message.add_alternative(html_content, subtype="html")

        return message

    async def _send_email(
        self,
        recipient: str,
        subject: str,
        template_name: str,
        **kwargs,
    ) -> None:
        message = self.build_message(recipient, subject, template_name, **kwargs)
        await self.client.send(message)

    async def send_verification_email(self, recipient: str, **kwargs) -> None:
        await self._send_email(
            recipient=recipient,
            subject="Verify your email",
            template_name="verify_email",
            **kwargs,
        )


mail_client = get_mail_client()


@lru_cache
def get_mail_service() -> MailService:
    return MailService(client=mail_client)
