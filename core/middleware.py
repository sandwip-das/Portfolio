import datetime
from django.utils import timezone
from .models import SiteVisitorTrack

class SiteVisitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignore admin, static, media and common non-human paths
        path = request.path
        if any(path.startswith(prefix) for prefix in ['/admin/', '/static/', '/media/', '/_nested_admin/', '/favicon.ico']):
            return self.get_response(request)

        # Process the request
        # Ensure session exists
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        # Try to find an active track for this session in the last 30 minutes
        thirty_minutes_ago = timezone.now() - datetime.timedelta(minutes=30)
        track = SiteVisitorTrack.objects.filter(
            session_key=session_key,
            last_activity__gte=thirty_minutes_ago
        ).order_by('-last_activity').first()

        if track:
            # Update existing track
            track.last_activity = timezone.now()
            # If they just moved to a new path, maybe we should track it? 
            # But the user wants "duration" which usually implies a session. 
            # If we want path-level tracking, we'd need multiple records. 
            # Let's keep it simple: one record per session per "session start".
            
            # Update user info if they logged in during the session
            if request.user.is_authenticated and not track.user:
                track.user = request.user
                track.name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                track.email = request.user.email
                if hasattr(request.user, 'profile'):
                    track.contact_number = request.user.profile.contact_number
            track.save()
        else:
            # Create new track
            name = ""
            email = ""
            contact_number = ""
            if request.user.is_authenticated:
                name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                email = request.user.email
                if hasattr(request.user, 'profile'):
                    contact_number = request.user.profile.contact_number

            SiteVisitorTrack.objects.create(
                user=request.user if request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                browsing_source=request.META.get('HTTP_REFERER', ''),
                path=path,
                session_key=session_key,
                name=name,
                email=email,
                contact_number=contact_number
            )

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
