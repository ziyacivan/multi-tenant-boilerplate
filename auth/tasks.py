from celery import shared_task

from utils.services import EmailService


@shared_task
def send_verification_email_task(
    email: str, verification_code: str, verification_code_expires_at
):
    email_service = EmailService()
    email_service.send_verification_email(
        email=email,
        verification_code=verification_code,
        expires_at=verification_code_expires_at,
    )
