from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, blog_detail, custom_signup, verify_registration_otp

# Admin Customization
admin.site.site_header = "My Portfolio administration"
admin.site.site_title = "My Portfolio administration"
admin.site.index_title = "Welcome to My Portfolio administration"

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),
    path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('_nested_admin/', include('nested_admin.urls')),
    
    # Custom Auth Overrides
    path('accounts/signup/', include([
        path('', custom_signup, name='account_signup'),
    ])),
    path('accounts/verify-registration-otp/', verify_registration_otp, name='verify_registration_otp'),
    
    path('accounts/', include('allauth.urls')),
    path('core/', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
