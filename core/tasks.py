# core/tasks.py
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings as django_settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_email_task(subject, body, to_email=None, reply_to=None):
    if to_email is None:
        to_email = [getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com')]
    elif isinstance(to_email, str):
        to_email = [to_email]

    from_email = getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@portfolio.com')

    try:
        email_msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to_email,
            reply_to=reply_to if isinstance(reply_to, list) else ([reply_to] if reply_to else None)
        )
        email_msg.send(fail_silently=False)
        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        print(f"Email sending failed: {str(e)}")