from pydantic import Field, SecretStr


class MailingSettings:
    smtp_host: str
    smtp_port: int = Field(gt=0, lt=65536)
    smtp_username: str
    smtp_password: SecretStr | None = None
    smtp_use_tls: bool

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_admin: str,
        smtp_username: str,
        smtp_password: SecretStr,
        smtp_use_tls: bool,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_admin = smtp_admin
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls
