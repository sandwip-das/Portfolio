import logging
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def get_admin_email():
    """Returns the first superuser's email, or DEFAULT_FROM_EMAIL as fallback."""
    superuser = User.objects.filter(is_superuser=True).order_by('id').first()
    if superuser and superuser.email:
        return superuser.email
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com')


def send_portfolio_email(subject, body, to_email=None, reply_to=None):
    """
    Send email via Django's integrated email backend.
    Works seamlessly with Brevo SMTP relay configured via EMAIL_* settings.
    """
    if not to_email:
        logger.warning("send_portfolio_email called with no recipient.")
        return

    # Use DEFAULT_FROM_EMAIL from settings
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
    
    headers = {}
    if reply_to:
        headers['Reply-To'] = reply_to

    try:
        from django.core.mail import EmailMessage
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email],
            headers=headers
        )
        email.send(fail_silently=False)
        logger.info(f"Email sent successfully to {to_email} | Subject: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")