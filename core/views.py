from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.utils import timezone

import uuid
import random
from .models import (
    HomeSettings, Skill, Project, SkillCategory, Experience, Service, ServiceBooking,
    ContactMessage, AcademicBackground, ProfessionalTraining, BlogPost, Review, BlogViewTrack,
    BlogReaction, BlogComment, UserProfile, CommentReaction, PendingRegistration, Hero
)
from .forms import ServiceBookingForm, ContactForm, ReviewForm
from .utils import send_portfolio_email, get_admin_email
from .templatetags.core_tags import smart_url

def favicon_view(request):
    """
    Dynamic favicon view to satisfy browsers (like Edge) that hard-code 
    requests to /favicon.ico.
    """
    settings_obj = HomeSettings.load()
    if settings_obj.favicon:
        return redirect(smart_url(settings_obj.favicon))
    return redirect('/static/favicon.ico')


# ===================== Helper Functions =====================
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


# ===================== Home Page & Forms =====================
def home(request):
    admin_email = get_admin_email()
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        # --------------------- Service Booking ---------------------
        if 'service_id' in request.POST:
            form = ServiceBookingForm(request.POST)
            if form.is_valid():
                booking = form.save(commit=False)
                try:
                    service = Service.objects.get(id=request.POST.get('service_id'))
                    booking.service = service
                    booking.save()

                    # Format date & time
                    if booking.date_from == booking.date_to:
                        booking_date = booking.date_from.strftime('%d-%b-%y')
                    else:
                        booking_date = f"{booking.date_from.strftime('%d-%b-%y')} to {booking.date_to.strftime('%d-%b-%y')}"
                    booking_time = f"{booking.time_from.strftime('%I:%M %p')} to {booking.time_to.strftime('%I:%M %p')}"

                    # Notify Superuser
                    subject = f"New Service Booking: {service.title} from {booking.name}"
                    body = f"""You have received a new service booking request.

Service: {service.title}
Name: {booking.name}
Phone: {booking.phone}
Email: {booking.email}
Date: {booking_date}
Time: {booking_time}
Message: {booking.additional_message}

Review in admin panel: {request.build_absolute_uri(reverse('admin:core_servicebooking_changelist'))}
"""
                    send_portfolio_email(subject, body, to_email=admin_email, reply_to=booking.email)

                    # Acknowledgment to User
                    user_subject = f"Booking Request Received: {service.title}"
                    user_body = f"""Hello {booking.name},

We have successfully received your booking request for '{service.title}' on {booking_date} at {booking_time}.

Your request is currently under review. You will receive a confirmation email once it is approved.

Best regards,
Sandwip Das
"""
                    send_portfolio_email(user_subject, user_body, to_email=booking.email)

                    if is_ajax:
                        return JsonResponse({'status': 'success', 'message': "Your booking request has been submitted successfully!"})
                    messages.success(request, "Your booking request has been submitted successfully!")
                    return redirect('home')
                except Service.DoesNotExist:
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': "Selected service does not exist."}, status=400)
                    messages.error(request, "Selected service does not exist.")
                except Exception as e:
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': f"An unexpected error occurred: {str(e)}"}, status=500)
                    messages.error(request, f"An unexpected error occurred: {str(e)}")
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': "Please fix the errors in the booking form.", 'errors': form.errors}, status=400)
                messages.error(request, "Please fix the errors in the booking form.")


        # --------------------- Contact Form ---------------------
        elif 'contact_form' in request.POST:
            form = ContactForm(request.POST)
            if form.is_valid():
                contact = form.save()

                try:
                    # Email to Superuser
                    subject_admin = f"New Contact Message from {contact.name}"
                    body_admin = f"""You have received a new message from your portfolio website contact form.

Sender Details:
Name: {contact.name}
Email: {contact.email}
Phone: {contact.phone if contact.phone else 'Not provided'}
Subject: {contact.subject}

Message:
{contact.message}
"""
                    send_portfolio_email(subject_admin, body_admin, to_email=admin_email, reply_to=contact.email)

                    # Acknowledgment to User
                    subject_user = f"Thank you for contacting us, {contact.name}!"
                    body_user = f"""Hello {contact.name},

Thank you for reaching out! We have successfully received your message regarding '{contact.subject}'.

We will review your message and get back to you as soon as possible.

Best regards,
Sandwip Das
"""
                    send_portfolio_email(subject_user, body_user, to_email=contact.email)

                    if is_ajax:
                        return JsonResponse({'status': 'success', 'message': "Your message has been sent successfully!"})
                    messages.success(request, "Your message has been sent successfully!")
                    return redirect('home')
                except Exception as e:
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': f"An unexpected error occurred: {str(e)}"}, status=500)
                    messages.error(request, f"An unexpected error occurred: {str(e)}")
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': "Please fix the errors in the contact form."}, status=400)
                messages.error(request, "Please fix the errors in the contact form.")

        elif 'review_form' in request.POST:
            form = ReviewForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    form.save()
                    if is_ajax:
                        return JsonResponse({'status': 'success', 'message': "Your review has been submitted for approval."})
                    messages.success(request, "Your review has been submitted for approval.")
                    return redirect('home')
                except Exception as e:
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': f"An unexpected error occurred: {str(e)}"}, status=500)
                    messages.error(request, f"An unexpected error occurred: {str(e)}")
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': "Please fix the errors in the review form."}, status=400)
                messages.error(request, "Please fix the errors in the review form.")

    # ===================== Context Rendering =====================
    context = {
        'hero': Hero.objects.first(),
        'skills': Skill.objects.all(),
        'skill_categories': SkillCategory.objects.all().prefetch_related('items'),
        'projects': Project.objects.all().order_by('-created_at'),
        'experiences': Experience.objects.all(),
        'services': Service.objects.all(),
        'academic_background': AcademicBackground.objects.all(),
        'professional_trainings': ProfessionalTraining.objects.filter(category='TRAINING'),
        'global_certifications': ProfessionalTraining.objects.filter(category='CERTIFICATION'),
        'blog_posts': BlogPost.objects.all().order_by('-created_at'),
        'booking_form': ServiceBookingForm(),
        'contact_form': ContactForm(),
        'review_form': ReviewForm(),
        'reviews': Review.objects.filter(is_approved=True),
    }
    return render(request, 'home.html', context)


# ===================== Blog Detail =====================
def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    BlogViewTrack.objects.create(
        post=post,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        browsing_source=request.META.get('HTTP_REFERER', ''),
        contact_number=getattr(request.user.profile, 'contact_number', None) if request.user.is_authenticated else None
    )
    post.views += 1
    post.save()
    return render(request, 'blog_detail.html', {'post': post})


# ===================== Blog Reactions & Comments =====================
@login_required
def toggle_reaction(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    reaction_type = request.POST.get('reaction')
    reaction, created = BlogReaction.objects.get_or_create(post=post, user=request.user, defaults={'reaction': reaction_type})
    if not created:
        if reaction.reaction == reaction_type:
            reaction.delete()
        else:
            reaction.reaction = reaction_type
            reaction.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'likes': post.like_count, 'dislikes': post.dislike_count})
    return redirect('blog_detail', slug=post.slug)


@login_required
def toggle_comment_reaction(request, comment_id):
    comment = get_object_or_404(BlogComment, id=comment_id)
    reaction_type = request.POST.get('reaction')
    reaction, created = CommentReaction.objects.get_or_create(comment=comment, user=request.user, defaults={'reaction': reaction_type})
    if not created:
        if reaction.reaction == reaction_type:
            reaction.delete()
        else:
            reaction.reaction = reaction_type
            reaction.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'likes': comment.like_count, 'dislikes': comment.dislike_count})
    return redirect('blog_detail', slug=comment.post.slug)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    content = request.POST.get('content')
    parent_id = request.POST.get('parent_id')
    parent_comment = BlogComment.objects.filter(id=parent_id).first() if parent_id else None
    if content:
        comment = BlogComment.objects.create(post=post, user=request.user, content=content, parent=parent_comment)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'comment_id': comment.id,
                'username': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime("%b %d, %Y %I:%M %p"),
                'total_comments': post.comment_count
            })
    return redirect('blog_detail', slug=post.slug)


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(BlogComment, id=comment_id, user=request.user)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            comment.content = content
            comment.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'content': comment.content})
    return redirect('blog_detail', slug=comment.post.slug)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(BlogComment, id=comment_id, user=request.user)
    slug = comment.post.slug
    comment.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('blog_detail', slug=slug)


# ===================== OTP & Password Reset =====================
def send_otp_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            otp = str(random.randint(100000, 999999))
            cache.set(f"otp_{email}", otp, timeout=300)
            subject = "Password Reset OTP — Portfolio"
            message = f"""Hello {user.username},

Your OTP code for password reset is:

    {otp}

This code is valid for 5 minutes. Do not share it with anyone.

If you did not request a password reset, please ignore this email.

Best regards,
Sandwip Das
"""
            send_portfolio_email(subject, message, to_email=email)
            return render(request, "auth/verify_otp.html", {"email": email, "otp_type": "forgot_password"})
        messages.error(request, "No account found with this email address.")
    return render(request, "auth/send_otp.html")


def resend_forgot_password_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            otp = str(random.randint(100000, 999999))
            cache.set(f"otp_{email}", otp, timeout=300)
            subject = "Resend: Password Reset OTP — Portfolio"
            message = f"""Hello {user.username},

Your new OTP code for password reset is:

    {otp}

This code is valid for 5 minutes.

Best regards,
Sandwip Das
"""
            send_portfolio_email(subject, message, to_email=email)
            messages.success(request, "A new OTP has been sent to your email.")
        else:
            messages.error(request, "No account found with this email address.")
    return render(request, "auth/verify_otp.html", {"email": email if 'email' in dir() else '', "otp_type": "forgot_password"})


def verify_otp_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        cached_otp = cache.get(f"otp_{email}")
        if cached_otp and cached_otp == otp:
            cache.delete(f"otp_{email}")
            request.session['reset_email'] = email
            return redirect('reset_password_otp')
        messages.error(request, "Invalid or expired OTP. Please try again.")
        return render(request, "auth/verify_otp.html", {"email": email, "otp_type": "forgot_password"})
    return redirect('send_otp')


def reset_password_otp(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('send_otp')
    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password and len(password) >= 8:
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(password)
                user.save()
                del request.session['reset_email']
                messages.success(request, "Password reset successfully! You can now log in.")
                return redirect('account_login')
        else:
            messages.error(request, "Passwords do not match or must be at least 8 characters.")
    return render(request, "auth/reset_password.html")


# ===================== User Signup (Simplified) =====================
def custom_signup(request):
    if request.user.is_authenticated:
        return redirect('my_blog')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()

        # Validation
        if not username or not email:
            messages.error(request, "Please enter both username and email.")
            return render(request, 'account/signup.html', {'form_data': request.POST})

        user = User.objects.filter(email=email).first()
        if user:
            # If user already exists, just log them in
            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('my_blog')

        # Unique username generation
        base_username = username
        final_username = base_username
        counter = 1
        while User.objects.filter(username=final_username).exists():
            final_username = f"{base_username}{counter}"
            counter += 1

        # Create user with random password
        random_password = str(uuid.uuid4())
        user = User.objects.create(
            username=final_username,
            email=email,
            password=make_password(random_password),
            first_name=username,
        )
        
        # Mark email as verified for allauth
        from allauth.account.models import EmailAddress
        EmailAddress.objects.get_or_create(
            user=user, email=user.email,
            defaults={'verified': True, 'primary': True}
        )

        from django.contrib.auth import login
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Account created successfully! Welcome to the blog.")
        return redirect('my_blog')

    return render(request, 'account/signup.html')


def verify_registration_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        cached_otp = cache.get(f"reg_otp_{email}")

        if cached_otp and cached_otp == otp:
            pending = PendingRegistration.objects.filter(email=email).first()
            if not pending:
                messages.error(request, "Registration session expired. Please sign up again.")
                return redirect('account_signup')

            if pending.is_expired():
                pending.delete()
                messages.error(request, "Registration session expired. Please sign up again.")
                return redirect('account_signup')

            from allauth.account.models import EmailAddress
            user = User.objects.create(
                username=pending.username,
                email=pending.email,
                password=pending.password,
                first_name=pending.full_name,
            )
            if pending.profile_picture:
                try:
                    user.profile.profile_picture = pending.profile_picture
                    user.profile.save()
                except Exception:
                    pass

            EmailAddress.objects.get_or_create(
                user=user, email=user.email,
                defaults={'verified': True, 'primary': True}
            )

            cache.delete(f"reg_otp_{email}")
            pending.delete()

            messages.success(request, "Account verified successfully! You can now log in.")
            return redirect('account_login')

        messages.error(request, "Invalid or expired OTP. Please try again.")
        return render(request, 'account/verify_registration_otp.html', {'email': email})
    return redirect('account_signup')


def resend_registration_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        pending = PendingRegistration.objects.filter(email=email).first()
        if pending:
            otp = str(random.randint(100000, 999999))
            cache.set(f"reg_otp_{email}", otp, timeout=300)
            subject = "Resend: Verify Your Account — Portfolio"
            body = f"""Hello {pending.full_name},

Your new OTP for account verification is:

    {otp}

This code is valid for 5 minutes.

Best regards,
Sandwip Das
"""
            send_portfolio_email(subject, body, to_email=email)
            messages.success(request, "A new OTP has been sent to your email.")
        else:
            messages.error(request, "Registration session not found. Please sign up again.")
    return render(request, 'account/verify_registration_otp.html', {'email': email if 'email' in dir() else ''})


# ===================== Profile =====================
@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.contact_number = request.POST.get('contact_number', '')
        profile.profession = request.POST.get('profession', '')
        profile.organization = request.POST.get('organization', '')
        profile.interest_field = request.POST.get('interest_field', '')
        profile.highest_degree = request.POST.get('highest_degree', '')
        profile.location = request.POST.get('location', '')
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('edit_profile')
    return render(request, 'account/profile.html', {'profile': profile})


# ===================== My Blog =====================
@login_required
def my_blog(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    posts = BlogPost.objects.all().order_by('-created_at')
    if query:
        posts = posts.filter(title__icontains=query)
    if category:
        posts = posts.filter(category=category)
    categories = BlogPost.objects.values_list('category', flat=True).distinct()
    return render(request, 'my_blog.html', {
        'posts': posts,
        'query': query,
        'category_filter': category,
        'categories': categories
    })

def blog_suggestions(request):
    from django.http import JsonResponse
    query = request.GET.get('q', '')
    if len(query) < 1:
        return JsonResponse([], safe=False)
    suggestions = BlogPost.objects.filter(title__icontains=query).values('title', 'slug')[:10]
    return JsonResponse(list(suggestions), safe=False)