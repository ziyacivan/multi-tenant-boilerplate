from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


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
