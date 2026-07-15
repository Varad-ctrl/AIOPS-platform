"""
Sends alert emails over SMTP. Works with Gmail, Microsoft 365, or any
standard SMTP relay - just set SMTP_HOST/PORT/USER/PASSWORD in .env.

If SMTP isn't configured, send_email() logs and no-ops instead of raising,
so the rest of the alert pipeline (DB write, in-app alert) keeps working
even before email is set up.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("email_service")


class EmailService:
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL

    @property
    def configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        if not self.configured:
            logger.warning("smtp_not_configured", to=to_email, subject=subject)
            return False

        message = MIMEMultipart()
        message["From"] = self.from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, to_email, message.as_string())
            logger.info("email_sent", to=to_email, subject=subject)
            return True
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("email_send_failed", to=to_email, subject=subject, error=str(exc))
            return False


def build_alert_email(
    alert_title: str, severity: str, description: str, source: str
) -> tuple[str, str]:
    """Builds (subject, body) for an alert notification, following the
    format specified in the roadmap (pod failure / node failure / etc)."""
    icon = "🚨" if severity in ("critical", "high") else "⚠️"
    subject = f"{icon} {severity.title()}: {alert_title}"
    body = (
        f"Alert: {alert_title}\n"
        f"Severity: {severity}\n"
        f"Source: {source}\n\n"
        f"Details:\n{description}\n\n"
        f"— AIOps Assistant"
    )
    return subject, body
