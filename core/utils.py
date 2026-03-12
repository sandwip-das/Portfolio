from django.core.mail import EmailMessage
from django.conf import settings as django_settings
from django.contrib.auth.models import User
from .tasks import send_email_task



def get_admin_email():
    admin_email = getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'admin@example.com')
    superuser = User.objects.filter(is_superuser=True).order_by('id').first()
    if superuser and superuser.email:
        admin_email = superuser.email
    return admin_email

def send_portfolio_email(subject, body, to_email=None, reply_to=None):
    """
    Async email sending using Celery
    """
    send_email_task.delay(subject, body, to_email, reply_to)