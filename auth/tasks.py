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


@shared_task
def send_reset_email_task(user_id: int, reset_url: str):
    from users.models import User
    
    email_service = EmailService()
    try:
        user = User.objects.get(id=user_id)
        email_service.send_reset_email(user, reset_url)
    except User.DoesNotExist:
        pass
