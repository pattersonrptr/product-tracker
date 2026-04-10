"""Email notification service using SendGrid."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, Email, Mail, To

from src.config import settings
from src.config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EmailResult:
    """Result of an email send attempt."""

    success: bool
    status_code: int | None = None
    error_message: str | None = None


class EmailServiceInterface(ABC):
    """Abstract interface for email sending."""

    @abstractmethod
    def send_price_alert_email(
        self,
        to_email: str,
        search_term: str,
        product_title: str,
        product_price: float,
        max_price: float,
        product_url: str,
        source_website_name: str,
    ) -> EmailResult:
        """Send a price alert notification email."""
        ...


class SendGridEmailService(EmailServiceInterface):
    """SendGrid implementation of the email service."""

    def __init__(
        self,
        api_key: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
    ):
        self.api_key = api_key or settings.SENDGRID_API_KEY
        self.from_email = from_email or settings.FROM_EMAIL
        self.from_name = from_name or settings.NOTIFICATION_FROM_NAME

    def _build_html_content(
        self,
        search_term: str,
        product_title: str,
        product_price: float,
        max_price: float,
        product_url: str,
        source_website_name: str,
    ) -> str:
        """Build HTML email body for a price alert match."""
        savings = max_price - product_price
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header {{ background: #1976d2; color: #fff; padding: 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .body {{ padding: 24px; }}
        .highlight {{ background: #e8f5e9; border-left: 4px solid #4caf50; padding: 16px; margin: 16px 0; border-radius: 4px; }}
        .price {{ font-size: 28px; color: #2e7d32; font-weight: bold; }}
        .savings {{ color: #f57c00; font-weight: bold; }}
        .btn {{ display: inline-block; background: #1976d2; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 16px; }}
        .footer {{ background: #f4f4f4; padding: 16px; text-align: center; font-size: 12px; color: #999; }}
        .details {{ margin: 16px 0; }}
        .details td {{ padding: 4px 8px; }}
        .details td:first-child {{ font-weight: bold; color: #555; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Oportunidade encontrada!</h1>
        </div>
        <div class="body">
            <p>Olá! Encontramos um produto abaixo do seu preço alvo para a busca <strong>"{search_term}"</strong>.</p>

            <div class="highlight">
                <p style="margin:0 0 8px 0;"><strong>{product_title}</strong></p>
                <p class="price" style="margin:0;">R$ {product_price:,.2f}</p>
                <p class="savings" style="margin:8px 0 0 0;">Economia de R$ {savings:,.2f} em relação ao seu alerta (R$ {max_price:,.2f})</p>
            </div>

            <table class="details">
                <tr><td>Site:</td><td>{source_website_name}</td></tr>
                <tr><td>Preço máximo do alerta:</td><td>R$ {max_price:,.2f}</td></tr>
                <tr><td>Preço encontrado:</td><td>R$ {product_price:,.2f}</td></tr>
            </table>

            <a href="{product_url}" class="btn">Ver produto →</a>
        </div>
        <div class="footer">
            <p>Você recebeu este e-mail porque configurou um alerta de preço no Garimpei.</p>
            <p>Limite de envio: 1 e-mail por alerta a cada hora.</p>
        </div>
    </div>
</body>
</html>"""

    def send_price_alert_email(
        self,
        to_email: str,
        search_term: str,
        product_title: str,
        product_price: float,
        max_price: float,
        product_url: str,
        source_website_name: str,
    ) -> EmailResult:
        """Send a price alert notification email via SendGrid."""
        if not self.api_key:
            logger.warning("SendGrid API key not configured, skipping email send")
            return EmailResult(
                success=False,
                error_message="SendGrid API key not configured",
            )

        subject = (
            f"🎯 Oportunidade! {search_term} por R$ {product_price:,.2f}"
            f" no {source_website_name}"
        )

        html_content = self._build_html_content(
            search_term=search_term,
            product_title=product_title,
            product_price=product_price,
            max_price=max_price,
            product_url=product_url,
            source_website_name=source_website_name,
        )

        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content),
        )

        try:
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)

            logger.info(
                "Email sent to %s for alert '%s' (status=%s)",
                to_email,
                search_term,
                response.status_code,
            )
            return EmailResult(
                success=response.status_code in (200, 201, 202),
                status_code=response.status_code,
            )
        except Exception as e:
            logger.error(
                "Failed to send email to %s: %s",
                to_email,
                str(e),
            )
            return EmailResult(
                success=False,
                error_message=str(e),
            )
