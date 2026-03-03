from django.core.mail import EmailMessage
from django.conf import settings as django_settings
from django.contrib.auth.models import User

def get_admin_email():
    """
    Returns the email address of the first superuser.
    Falls back to DEFAULT_FROM_EMAIL.
    """
    admin_email = getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com')
    superuser = User.objects.filter(is_superuser=True).order_by('id').first()
    if superuser and superuser.email:
        admin_email = superuser.email
    return admin_email

def send_portfolio_email(subject, body, to_email=None, reply_to=None):
    """
    Helper function to send emails from the portfolio.
    """
    if to_email is None:
        to_email = [get_admin_email()]
    elif isinstance(to_email, str):
        to_email = [to_email]

    from_email = getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@portfolio.com')
    
    email_msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to_email,
        reply_to=reply_to if isinstance(reply_to, list) else ([reply_to] if reply_to else None)
    )
    return email_msg.send(fail_silently=False)
