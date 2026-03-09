import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
try:
    from django.conf import settings
    print("INSTALLED_APPS:", settings.INSTALLED_APPS)
    django.setup()
    print("Django setup successful")
except Exception as e:
    import traceback
    traceback.print_exc()
