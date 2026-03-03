from django.utils import timezone
import datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


from django.core.cache import cache
import random

from allauth.account.signals import user_signed_up
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

@receiver(pre_delete, sender=User)
def clean_user_data(sender, instance, **kwargs):
    """
    Ensures a Hard Delete:
    When a user is deleted from the admin panel, we wipe all caches and 
    related data to ensure they must go through the full verification process again.
    """
    # 1. Clear any OTP or Registration caches for this email
    cache.delete(f"otp_{instance.email}")
    cache.delete(f"reg_otp_{instance.email}")
    
    # 2. Delete any hanging PendingRegistration records
    PendingRegistration.objects.filter(email=instance.email).delete()

class UserManagement(User):
    class Meta:
        proxy = True
        verbose_name = 'User Management'
        verbose_name_plural = 'User Management'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profiles/', default='default_profile.png', blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    organization = models.CharField(max_length=100, blank=True, null=True)
    interest_field = models.CharField(max_length=100, blank=True, null=True)
    highest_degree = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(user_signed_up)
def populate_profile(request, user, **kwargs):
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if 'full_name' in request.POST:
        full_name = request.POST['full_name'].strip()
        # username: replace spaces with hyphens, limit to first 2 words
        words = full_name.split()
        formatted_username = "-".join(words[:2])
        user.username = formatted_username
        user.save()
        
    if request.FILES.get('profile_picture'):
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()

from django.db.models.signals import post_save

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        try:
            instance.profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)

class PendingRegistration(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    password = models.CharField(max_length=255) # Store hashed password
    full_name = models.CharField(max_length=255)
    profile_picture = models.ImageField(upload_to='profiles/pending/', null=True, blank=True)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.utils import timezone
        import datetime
        return timezone.now() > self.created_at + datetime.timedelta(minutes=2)

    def __str__(self):
        return f"Pending: {self.username} ({self.email})"

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk and self.__class__.objects.exists():
            # If you want to prevent creation of more than one object:
            raise ValidationError(f"There can be only one {self.__class__.__name__} instance")
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class HomeSettings(SingletonModel):
    # Site Config
    site_title = models.CharField(max_length=100, default="Portfolio", help_text="Shown in the browser tab")
    nav_name = models.CharField(max_length=100, default="Portfolio", help_text="The name shown in the navigation bar")
    
    logo = models.ImageField(upload_to='core/site/', blank=True, help_text="The main logo of the site")
    favicon = models.ImageField(upload_to='core/site/', blank=True)
    
    # Hero Section
    hero_greeting = models.CharField(max_length=100, default="Hello, I am")
    hero_name = models.CharField(max_length=100, default="Your Name")
    hero_description = models.TextField(blank=True)
    hero_bg_image = models.ImageField(upload_to='core/hero/', blank=True, help_text="Background image for hero section")
    hero_profile_image = models.ImageField(upload_to='core/hero/', blank=True, help_text="Your transparent profile picture")
    resume_file = models.FileField(upload_to='core/docs/', blank=True, help_text="Your CV/Resume")
    
    # About Section
    about_title = models.CharField(max_length=100, default="About Me")
    about_description = models.TextField(blank=True)
    about_who_am_i = models.TextField(blank=True, help_text="Text for the 'Who am I?' section")
    
    # Contact Section Info
    contact_heading = models.CharField(max_length=100, default="Let's Connect!")
    contact_sub_heading = models.CharField(max_length=100, blank=True)
    contact_text = models.TextField(blank=True, help_text="Text shown below the sub-heading")
    
    # Skills/Services/Projects Intro Text
    technical_skills_description = models.TextField(blank=True, help_text="Intro text for the Technical Skills section")
    services_description = models.TextField(blank=True, help_text="Intro text for the My Services section")
    projects_description = models.TextField(blank=True, help_text="Intro text for the Featured Projects section")

    # Social Media Links & Logos
    linkedin_url = models.URLField(blank=True, help_text="LinkedIn Profile URL")
    linkedin_logo = models.ImageField(upload_to='core/social/', blank=True, help_text="LinkedIn Logo (Transparent Background)")
    facebook_url = models.URLField(blank=True, help_text="Facebook Profile URL")
    facebook_logo = models.ImageField(upload_to='core/social/', blank=True, help_text="Facebook Logo (Transparent Background)")
    github_url = models.URLField(blank=True, help_text="GitHub Profile URL")
    github_logo = models.ImageField(upload_to='core/social/', blank=True, help_text="GitHub Logo (Transparent Background)")
    instagram_url = models.URLField(blank=True, help_text="Instagram Profile URL")
    instagram_logo = models.ImageField(upload_to='core/social/', blank=True, help_text="Instagram Logo (Transparent Background)")
    x_url = models.URLField(blank=True, help_text="X (Twitter) Profile URL")
    x_logo = models.ImageField(upload_to='core/social/', blank=True, help_text="X (Twitter) Logo (Transparent Background)")
    
    # Footer
    footer_copyright = models.CharField(max_length=200, default="© 2026 All Rights Reserved.")

    # Blog Section
    blog_section_title = models.CharField(max_length=100, default="My Blog")
    blog_section_description = models.TextField(blank=True, help_text="About My Blog - shown under the My Blog container")

    def __str__(self):
        return "Home Page Configuration"

    class Meta:
        verbose_name = "Home Page Content"
        verbose_name_plural = "Home Page Content"

class NavbarMenu(models.Model):
    settings = models.ForeignKey(HomeSettings, on_delete=models.CASCADE, default=1, related_name='navbar_menus')
    name = models.CharField(max_length=50, verbose_name="Menu Name")
    section_id = models.CharField(max_length=50, blank=True, help_text="HTML ID (auto-generated if empty). Use: 'home', 'about', 'experience', 'skills', 'projects', 'service', 'blog', 'contact' for existing sections.")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"

    def __str__(self):
        return self.name

# --- PROXY MODELS FOR ADMIN REORDER ---

class NavbarSettings(HomeSettings):
    class Meta:
        proxy = True
        verbose_name = "Navbar Settings"
        verbose_name_plural = "Navbar Settings"

class HeroMainSettings(HomeSettings):
    class Meta:
        proxy = True
        verbose_name = "Hero Main"
        verbose_name_plural = "Hero Main"

class HeroSocialSettings(HomeSettings):
    class Meta:
        proxy = True
        verbose_name = "Social Media"
        verbose_name_plural = "Social Media"

class AboutSectionSettings(HomeSettings):
    class Meta:
        proxy = True
        verbose_name = "About Me Main"
        verbose_name_plural = "About Me Main"



class ContactSectionSettings(HomeSettings):
    class Meta:
        proxy = True
        verbose_name = "Contact Menu"
        verbose_name_plural = "Contact Menu"

class FooterSettings(HomeSettings):
    class Meta:
        proxy = True
        verbose_name = "Footer Text"
        verbose_name_plural = "Footer Text"

# --- REAL MODELS & INLINES ---

class Experience(models.Model):
    company_name = models.CharField(max_length=200)
    company_logo = models.ImageField(upload_to='core/company_logos/', blank=True, null=True)
    designation = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank if currently working here")
    is_current = models.BooleanField(default=False, verbose_name="I currently work here")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.designation} at {self.company_name}"

    @property
    def duration_string(self):
        start_str = self.start_date.strftime('%b %Y')
        if self.is_current or not self.end_date:
            return f"{start_str} - Present"
        return f"{start_str} - {self.end_date.strftime('%b %Y')}"

    @property
    def description_list(self):
        return [line.strip() for line in self.description.split('\n') if line.strip()]

class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='core/projects/', help_text="Cover Image")
    tech_stack = models.CharField(max_length=200, help_text="Comma separated technologies")
    live_link = models.URLField(blank=True)
    repo_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def tech_list(self):
        return [tech.strip() for tech in self.tech_stack.split(',') if tech.strip()] if self.tech_stack else []

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='core/projects/gallery/')
    
    def __str__(self):
        return f"{self.project.title} Image"

class Service(models.Model):
    title = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50, default="fas fa-layer-group", help_text="Font Awesome class")
    features = models.TextField(help_text="One feature per line")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title
    
    @property
    def feature_list(self):
        return [f.strip() for f in self.features.split('\n') if f.strip()]

class ServiceBooking(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_from = models.DateField(default=datetime.date.today, verbose_name="Start Date")
    date_to = models.DateField(default=datetime.date.today, verbose_name="End Date")
    time_from = models.TimeField(default=datetime.time(9, 0), verbose_name="Start Time")
    time_to = models.TimeField(default=datetime.time(10, 0), verbose_name="End Time")
    additional_message = models.TextField(blank=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Service Booking"
        verbose_name_plural = "Service Bookings"

    def __str__(self):
        return f"{self.name} - {self.service.title}"

# INLINED MODELS (Linked to HomeSettings for grouping)

class AcademicBackground(models.Model):
    # Link to AboutSectionSettings (which is HomeSettings)
    settings = models.ForeignKey(HomeSettings, on_delete=models.CASCADE, default=1, related_name='academic_backgrounds')
    institution_name = models.CharField(max_length=200)
    institution_logo = models.ImageField(upload_to='core/academic/', blank=True, null=True)
    degree_name = models.CharField(max_length=200)
    institution_link = models.URLField(blank=True)
    description = models.TextField(help_text="Bullet points separated by new lines")
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Academic Background"
        ordering = ['order', 'institution_name']

    def __str__(self):
        return f"{self.degree_name} at {self.institution_name}"
    
    @property
    def description_list(self):
        return [line.strip() for line in self.description.split('\n') if line.strip()]

class SkillCategory(models.Model):
    settings = models.ForeignKey(HomeSettings, on_delete=models.CASCADE, default=1, related_name='skill_categories')
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Skill Category Label"
        verbose_name_plural = "Skill Category Labels"
        ordering = ['order', 'name']
        
    def __str__(self):
        return self.name


class SkillItem(models.Model):
    category = models.ForeignKey(SkillCategory, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Skill Item"
        verbose_name_plural = "Skill Items"
        
    def __str__(self):
        return self.name

class ProfessionalTraining(models.Model):
    settings = models.ForeignKey(HomeSettings, on_delete=models.CASCADE, default=1, related_name='professional_trainings')
    MODE_CHOICES = [('Online', 'Online'), ('Offline', 'Offline')]
    CATEGORY_CHOICES = [('TRAINING', 'Professional Training'), ('CERTIFICATION', 'Global Certification')]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='TRAINING')
    course_name = models.CharField(max_length=200)
    organization_name = models.CharField(max_length=200)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='Online')
    image = models.ImageField(upload_to='core/training/', blank=True, null=True)
    certification_link = models.URLField(blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Professional Training & Certifications"
        ordering = ['order', 'course_name']

    def __str__(self):
        return f"{self.course_name} from {self.organization_name}"

# PROXY MODELS FOR EXPERTISE Splitting
class ProfessionalTrainingModel(ProfessionalTraining): # Proxy Model
    class Meta:
        proxy = True
        verbose_name = "Professional Training"
        verbose_name_plural = "Professional Trainings"

class GlobalCertificationModel(ProfessionalTraining): # Proxy Model
    class Meta:
        proxy = True
        verbose_name = "Global Certification"
        verbose_name_plural = "Global Certifications"

class BlogPost(models.Model):
    settings = models.ForeignKey(HomeSettings, on_delete=models.CASCADE, default=1, related_name='blog_posts')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    content = RichTextField()
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Site Management"
        verbose_name_plural = "Blog Site Management"

    def __str__(self):
        return self.title

    @property
    def image(self):
        # Helper to get the main feature image (lowest order)
        first_img = self.images.order_by('order').first()
        if first_img:
            return first_img.image
        return None

    @property
    def like_count(self):
        return self.reactions.filter(reaction='like').count()

    @property
    def dislike_count(self):
        return self.reactions.filter(reaction='dislike').count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def view_count(self):
        return self.view_tracks.count()

class BlogPostImage(models.Model):
    post = models.ForeignKey(BlogPost, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='core/blog/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image {self.id}"

class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username}"

    @property
    def like_count(self):
        return self.comment_reactions.filter(reaction='like').count()

    @property
    def dislike_count(self):
        return self.comment_reactions.filter(reaction='dislike').count()

class CommentReaction(models.Model):
    REACTION_CHOICES = (
        ('like', 'Like'),
        ('dislike', 'Dislike')
    )
    comment = models.ForeignKey(BlogComment, related_name='comment_reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')

    def __str__(self):
        return f"{self.user.username} {self.reaction} comment {self.comment.id}"

class BlogReaction(models.Model):
    REACTION_CHOICES = (
        ('like', 'Like'),
        ('dislike', 'Dislike')
    )
    post = models.ForeignKey(BlogPost, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user') # One reaction per user per post

    def __str__(self):
        return f"{self.user.username}: {self.reaction}"

class BlogViewTrack(models.Model):
    post = models.ForeignKey(BlogPost, related_name='view_tracks', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    browsing_source = models.CharField(max_length=255, null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_info = self.user.username if self.user else "Anonymous"
        return f"View by {user_info}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

# Legacy Models
class Skill(models.Model):
    settings = models.ForeignKey(HomeSettings, on_delete=models.CASCADE, default=1, related_name='skills')
    name = models.CharField(max_length=50, verbose_name="Technology Name")
    image = models.ImageField(upload_to='core/skills/', verbose_name="Image")
    # Hidden fields (legacy support or internal)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=50, blank=True)
    dominant_color = models.CharField(max_length=7, blank=True, default='')
    order = models.IntegerField(default=0)
    
    class Meta: 
        ordering = ['order', 'name']
        verbose_name = "Skill Card"
        verbose_name_plural = "Skill Cards"

    def __str__(self): return self.name

class TechnicalSkillsSection(HomeSettings):
    class Meta:
        proxy = True
        verbose_name = "Technical Skills"
        verbose_name_plural = "Technical Skills"


class Review(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    profession = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    picture = models.ImageField(upload_to='core/reviews/', blank=True, null=True, help_text="Optional user picture")
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    comment = models.TextField(max_length=70, help_text="Short comment about the service")
    is_approved = models.BooleanField(default=True, help_text="Set to False to hide this review")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "User Review"
        verbose_name_plural = "User Reviews"

    def __str__(self):
        return f"{self.name} - {self.rating} Stars"
