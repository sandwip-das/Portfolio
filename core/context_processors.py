# core/context_processors.py
from .models import HomeSettings

def site_settings(request):
    # get the first HomeSettings object
    settings_obj = HomeSettings.objects.first()
    if not settings_obj:
        # create default instance if it doesn't exist
        settings_obj = HomeSettings.objects.create()
        
    ctx = {'settings': settings_obj}
    
    if request.user.is_authenticated and request.user.is_superuser:
        from .models import ServiceBooking, ContactMessage, Review
        
        notifications = []
        
        for b in ServiceBooking.objects.filter(is_read=False):
            notifications.append({
                'id': b.id,
                'type': 'booking',
                'sender': b.name,
                'service': b.service.title,
                'created_at': b.created_at
            })
            
        for c in ContactMessage.objects.filter(is_read=False):
            notifications.append({
                'id': c.id,
                'type': 'contact',
                'sender': c.name,
                'service': 'Contact Form',
                'created_at': c.created_at
            })
            
        for r in Review.objects.filter(is_read=False):
            notifications.append({
                'id': r.id,
                'type': 'review',
                'sender': r.name,
                'service': 'Review',
                'created_at': r.created_at
            })
            
        notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        ctx['admin_notifications'] = notifications
        ctx['admin_unread_count'] = len(notifications)
        
    return ctx
