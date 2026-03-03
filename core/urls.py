from django.urls import path
from . import views

urlpatterns = [
    path('blog/<int:post_id>/reaction/', views.toggle_reaction, name='toggle_reaction'),
    path('blog/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/reaction/', views.toggle_comment_reaction, name='toggle_comment_reaction'),
    path('profile/', views.edit_profile, name='edit_profile'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    path('auth/send-otp/', views.send_otp_forgot_password, name='send_otp'),
    path('auth/verify-otp/', views.verify_otp_forgot_password, name='verify_otp'),
    path('auth/reset-password/', views.reset_password_otp, name='reset_password_otp'),
    path('auth/resend-forgot-pwd-otp/', views.resend_forgot_password_otp, name='resend_forgot_password_otp'),

    path('auth/signup/', views.custom_signup, name='account_signup'),
    path('auth/verify-registration-otp/', views.verify_registration_otp, name='verify_registration_otp'),
    path('auth/resend-registration-otp/', views.resend_registration_otp, name='resend_registration_otp'),
    path('my-blog/', views.my_blog, name='my_blog'),
]
