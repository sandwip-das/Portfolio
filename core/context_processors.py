# core/context_processors.py
from .models import HomeSettings

def site_settings(request):
    # get the first HomeSettings object
    settings_obj = HomeSettings.objects.first()
    if not settings_obj:
        # create default instance if it doesn't exist
        settings_obj = HomeSettings.objects.create()
    return {'settings': settings_obj}
