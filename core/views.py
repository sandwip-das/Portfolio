from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import HomeSettings, Skill, Project, SkillCategory, Experience, Service, ServiceBooking, ContactMessage, AcademicBackground, ProfessionalTraining, BlogPost, Review, BlogViewTrack, BlogReaction, BlogComment, UserProfile, CommentReaction, PendingRegistration
from .forms import ServiceBookingForm, ContactForm, ReviewForm
from .utils import send_portfolio_email, get_admin_email
import uuid
import datetime
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.db import transaction

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
import random

def home(request):
    if request.method == 'POST':
        admin_email = get_admin_email()
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if 'service_id' in request.POST:
            form = ServiceBookingForm(request.POST)
            if form.is_valid():
                booking = form.save(commit=False)
                try:
                    service = Service.objects.get(id=request.POST.get('service_id'))
                    booking.service = service
                    booking.save()
                    
                    # Date and time formatting
                    if booking.date_from == booking.date_to:
                        booking_date = booking.date_from.strftime('%d-%b-%y')
                    else:
                        booking_date = f"{booking.date_from.strftime('%d-%b-%y')} to {booking.date_to.strftime('%d-%b-%y')}"
                    
                    booking_time = f"{booking.time_from.strftime('%I:%M %p')} to {booking.time_to.strftime('%I:%M %p')}"

                    # 1. Notify Admin
                    subject = f"New Service Booking: {service.title} from {booking.name}"
                    body = f"New booking request received:\n\nService: {service.title}\nName: {booking.name}\nPhone: {booking.phone}\nEmail: {booking.email}\nDate: {booking_date}\nTime: {booking_time}\nMessage: {booking.additional_message}\n\nReview this in the admin panel: {request.build_absolute_uri(reverse('admin:core_servicebooking_changelist'))}"
                    send_portfolio_email(subject, body, to_email=admin_email, reply_to=booking.email)

                    # 2. Acknowledgment to User
                    user_subject = f"Booking Request Received: {service.title}"
                    user_body = f"Hello {booking.name},\n\nWe have successfully received your booking request for '{service.title}' on {booking_date} at {booking_time}.\n\nYour request is currently under review. You will receive a confirmation email once it is approved.\n\nBest regards,\nPortfolio Team"
                    send_portfolio_email(user_subject, user_body, to_email=booking.email)
                    
                    if is_ajax:
                        return JsonResponse({'status': 'success', 'message': "Your booking request has been submitted successfully!"})
                    messages.success(request, "Your booking request has been submitted successfully!")
                    return redirect('home')
                except Service.DoesNotExist:
                    if is_ajax:
                        return JsonResponse({'status': 'error', 'message': "Selected service does not exist."}, status=400)
                    messages.error(request, "Selected service does not exist.")
        
        elif 'contact_form' in request.POST:
            form = ContactForm(request.POST)
            if form.is_valid():
                contact = form.save()
                subject = f"Portfolio Contact: {contact.subject} - from {contact.name}"
                body = f"""
You have received a new message from your portfolio website contact form.

--------------------------------------------------
SENDER DETAILS:
Name:    {contact.name}
Email:   {contact.email}
Phone:   {contact.phone if contact.phone else 'Not provided'}
Subject: {contact.subject}

--------------------------------------------------
MESSAGE:
{contact.message}

--------------------------------------------------
This email was sent automatically from your portfolio website.
"""
                send_portfolio_email(subject, body, to_email=admin_email, reply_to=contact.email)
                
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': "Your message has been sent successfully!"})
                messages.success(request, "Your message has been sent successfully!")
                return redirect('home')
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': "Please fix the errors in the contact form."}, status=400)
                messages.error(request, "Please fix the errors in the contact form.")

        elif 'review_form' in request.POST:
            form = ReviewForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                if is_ajax:
                    return JsonResponse({'status': 'success', 'message': "Your review has been submitted for approval."})
                messages.success(request, "Your review has been submitted for approval.")
                return redirect('home')
            else:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': "Please fix the errors in the review form."}, status=400)
                messages.error(request, "Please fix the errors in the review form.")

    skills = Skill.objects.all()
    skill_categories = SkillCategory.objects.all().prefetch_related('items')
    projects = Project.objects.all().order_by('-created_at')
    experiences = Experience.objects.all()
    services = Service.objects.all()
    academic_background = AcademicBackground.objects.all()
    professional_trainings = ProfessionalTraining.objects.filter(category='TRAINING')
    global_certifications = ProfessionalTraining.objects.filter(category='CERTIFICATION')
    blog_posts = BlogPost.objects.all().order_by('-created_at')
    reviews = Review.objects.filter(is_approved=True)
    
    booking_form = ServiceBookingForm()
    contact_form = ContactForm()
    review_form = ReviewForm()

    context = {
        'skills': skills,
        'skill_categories': skill_categories,
        'projects': projects,
        'experiences': experiences,
        'services': services,
        'academic_background': academic_background,
        'professional_trainings': professional_trainings,
        'global_certifications': global_certifications,
        'blog_posts': blog_posts,
        'booking_form': booking_form,
        'contact_form': contact_form,
        'review_form': review_form,
        'reviews': reviews,
    }
    return render(request, 'home.html', context)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    browsing_source = request.META.get('HTTP_REFERER', '')
    
    if request.user.is_authenticated:
        contact_num = getattr(request.user.profile, 'contact_number', None)
        BlogViewTrack.objects.create(
            post=post, user=request.user, 
            ip_address=ip_address, user_agent=user_agent, 
            browsing_source=browsing_source,
            contact_number=contact_num
        )
    else:
        BlogViewTrack.objects.create(post=post, user=None, ip_address=ip_address, user_agent=user_agent, browsing_source=browsing_source)

    post.views += 1
    post.save()
    return render(request, 'blog_detail.html', {'post': post})

@login_required
def toggle_reaction(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(BlogPost, id=post_id)
        reaction_type = request.POST.get('reaction') # 'like' or 'dislike'
        reaction, created = BlogReaction.objects.get_or_create(post=post, user=request.user, defaults={'reaction': reaction_type})
        if not created:
            if reaction.reaction == reaction_type:
                reaction.delete()
            else:
                reaction.reaction = reaction_type
                reaction.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'likes': post.like_count,
            'dislikes': post.dislike_count
        })
    return redirect('blog_detail', slug=post.slug)

@login_required
def add_comment(request, post_id):
    if request.method == "POST":
        post = get_object_or_404(BlogPost, id=post_id)
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        if content:
            parent_comment = None
            if parent_id:
                try:
                    parent_comment = BlogComment.objects.get(id=parent_id)
                except BlogComment.DoesNotExist:
                    pass
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
def toggle_comment_reaction(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(BlogComment, id=comment_id)
        reaction_type = request.POST.get('reaction') # 'like' or 'dislike'
        reaction, created = CommentReaction.objects.get_or_create(comment=comment, user=request.user, defaults={'reaction': reaction_type})
        if not created:
            if reaction.reaction == reaction_type:
                reaction.delete()
            else:
                reaction.reaction = reaction_type
                reaction.save()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'likes': comment.like_count,
                'dislikes': comment.dislike_count
            })
    return redirect('blog_detail', slug=comment.post.slug)

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(BlogComment, id=comment_id)
    if request.user == comment.user or request.user.is_superuser:
        if request.method == 'POST':
            content = request.POST.get('content')
            if content:
                comment.content = content
                comment.save()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'content': comment.content
                    })
    return redirect('blog_detail', slug=comment.post.slug)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(BlogComment, id=comment_id)
    post = comment.post
    if request.user == comment.user or request.user.is_superuser:
        if request.method == 'POST':
            comment.delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'total_comments': post.comment_count
                })
    return redirect('blog_detail', slug=post.slug)

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        new_username = request.POST.get('username', '').strip()
        if new_username and new_username != request.user.username:
            if User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                messages.error(request, f"The username '{new_username}' is already taken. Please choose another.")
                return redirect('edit_profile')
            request.user.username = new_username
            request.user.save()

        profile.contact_number = request.POST.get('contact_number', profile.contact_number)
        profile.profession = request.POST.get('profession', profile.profession)
        profile.organization = request.POST.get('organization', profile.organization)
        profile.interest_field = request.POST.get('interest_field', profile.interest_field)
        profile.highest_degree = request.POST.get('highest_degree', profile.highest_degree)
        profile.location = request.POST.get('location', profile.location)
            
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
            
        profile.save()
            
        messages.success(request, 'Profile updated successfully!')
        return redirect('edit_profile')
        
    return render(request, 'account/profile.html', {'profile': profile})

def send_otp_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            otp = str(random.randint(100000, 999999))
            cache.set(f"otp_{email}", otp, timeout=120)
            subject = "Password Reset OTP"
            message = f"Your OTP for password reset is {otp}. It is valid for 2 minutes."
            send_portfolio_email(subject, message, to_email=email)
            return render(request, "auth/verify_otp.html", {"email": email})
        messages.error(request, "No user found with this email.")
    return render(request, "auth/send_otp.html")

def verify_otp_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        cached_otp = cache.get(f"otp_{email}")
        if cached_otp and cached_otp == otp:
            cache.delete(f"otp_{email}")
            request.session['reset_email'] = email
            return redirect('reset_password_otp')
        messages.error(request, "Invalid or expired OTP.")
        return render(request, "auth/verify_otp.html", {"email": email})
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
                messages.success(request, "Password reset successfully. You can now log in.")
                return redirect('account_login') # using allauth default login
        else:
            messages.error(request, "Passwords do not match or are too short.")
    return render(request, "auth/reset_password.html")

def custom_signup(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        profile_picture = request.FILES.get('profile_picture')

        if not username:
            messages.error(request, "Please enter a username.")
            return render(request, 'account/signup.html', {'form_data': request.POST})

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'account/signup.html', {'form_data': request.POST})

        # Check Email Availability (only active users count)
        if User.objects.filter(email=email).exists():
            messages.error(request, "The email ID already exists. Please try with another email ID.")
            return render(request, 'account/signup.html', {'form_data': request.POST})

        # If username is taken, make it unique by appending a short suffix
        base_username = username
        final_username = base_username
        counter = 1
        while User.objects.filter(username=final_username).exists() or PendingRegistration.objects.filter(username=final_username).exists():
            final_username = f"{base_username}{counter}"
            counter += 1

        # Clean any pending registrations for the same email
        PendingRegistration.objects.filter(email=email).delete()

        token = str(uuid.uuid4())
        hashed_password = make_password(password1)
        
        pending = PendingRegistration(
            username=final_username,
            email=email,
            password=hashed_password,
            full_name=username,
            token=token
        )
        if profile_picture:
            pending.profile_picture = profile_picture
        pending.save()

        # Send Verification Email
        otp = str(random.randint(100000, 999999))
        cache.set(f"reg_otp_{email}", otp, timeout=120)

        subject = "Action Required: Verify Your Portfolio Account"
        body = f"""Hello {username},

Thank you for registering. Your OTP for account verification is {otp}. It is valid for 2 minutes.

If the OTP expires, you can request a new one on the verification page.

Best regards,
Sandwip Das Portfolio
"""
        send_portfolio_email(subject, body, to_email=email)
        
        return render(request, 'account/verify_registration_otp.html', {'email': email})

    return render(request, 'account/signup.html')

def verify_registration_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp = request.POST.get("otp")
        cached_otp = cache.get(f"reg_otp_{email}")
        
        if cached_otp and cached_otp == otp:
            cache.delete(f"reg_otp_{email}")
            
            pending = get_object_or_404(PendingRegistration, email=email)
            
            with transaction.atomic():
                user = User.objects.create(
                    username=pending.username,
                    email=pending.email,
                    password=pending.password
                )
                user.first_name = ""
                user.last_name = ""
                user.save()

                if pending.profile_picture:
                    user.profile.profile_picture.save(
                        pending.profile_picture.name.split('/')[-1],
                        pending.profile_picture,
                        save=True
                    )
                else:
                    user.profile.save()

                pending.delete()
            
            from django.contrib.auth import login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration Successful! Welcome to your blog.")
            return redirect('my_blog')
            
        messages.error(request, "Invalid or expired OTP.")
        return render(request, "account/verify_registration_otp.html", {"email": email})
    return redirect('account_signup')

def resend_registration_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if PendingRegistration.objects.filter(email=email).exists():
            otp = str(random.randint(100000, 999999))
            cache.set(f"reg_otp_{email}", otp, timeout=120)
            
            subject = "Action Required: Verify Your Portfolio Account"
            body = f"Your new OTP for registration is {otp}. It is valid for 2 minutes."
            send_portfolio_email(subject, body, to_email=email)
            return JsonResponse({"status": "success", "message": "OTP resent successfully."})
        return JsonResponse({"status": "error", "message": "Pending registration not found."}, status=400)
    return redirect('account_signup')

def resend_forgot_password_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            user = User.objects.filter(email=email).first()
            if user:
                otp = str(random.randint(100000, 999999))
                cache.set(f"otp_{email}", otp, timeout=120)
                subject = "Password Reset OTP"
                message = f"Your new OTP for password reset is {otp}. It is valid for 2 minutes."
                send_portfolio_email(subject, message, to_email=email)
                return JsonResponse({"status": "success", "message": "OTP resent successfully."})
        return JsonResponse({"status": "error", "message": "Email not found."}, status=400)
    return redirect('send_otp')

def my_blog(request):
    if not request.user.is_authenticated:
        return redirect('account_signup')
    blog_posts = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'my_blog.html', {'blog_posts': blog_posts})
