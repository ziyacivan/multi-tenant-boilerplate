from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from users.models import User


class EmailService:
    @staticmethod
    def send_verification_email(email: str, verification_code: str, expires_at) -> bool:
        subject = "Email Doğrulama Kodu"
        html_content = render_to_string(
            "emails/verification_email.html",
            {
                "verification_code": verification_code,
                "expires_at": expires_at,
                "email": email,
            },
        )
        text_content = strip_tags(html_content)

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_alternative(html_content, "text/html")

        try:
            email_message.send()
            return True
        except Exception as e:
            # Log error here
            return False

    @staticmethod
    def send_reset_email(user: User, reset_url: str):
        subject = _("Password Reset Request")
        message = (
            f"Hello {user.get_username()},\n\n"
            f"We received a request to reset your password. You can reset your password by clicking the link below:\n\n"
            f"{reset_url}\n\n"
            "If you did not request a password reset, please ignore this email.\n\n"
            "Best regards\n"
        )

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email_message.attach_alternative(message.replace("\n", "<br>"), "text/html")

        try:
            email_message.send()
        except Exception as e:
            # Log error here
            pass
