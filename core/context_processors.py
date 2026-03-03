from .models import HomeSettings

def site_settings(request):
    settings = HomeSettings.objects.first()
    if not settings:
        # Create a default instance if it doesn't exist
        settings = HomeSettings.objects.create()
    return {'settings': settings}
