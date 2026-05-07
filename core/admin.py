from django.contrib import admin
from django import forms
from django.db import models
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline
from .models import (
    HomeSettings, NavbarSettings, HeroMainSettings, HeroSocialSettings, 
    AboutSectionSettings, ContactSectionSettings, FooterSettings,
    Project, Service, ServiceBooking, ContactMessage,
    AcademicBackground, SkillCategory, Experience, 
    ProfessionalTraining, GlobalCertificationModel, ProfessionalTrainingModel, 
    BlogPost, ProjectImage, Skill, SkillItem, Review, NavbarMenu,
    BlogPostImage, BlogComment, BlogReaction, BlogViewTrack,
    UserProfile, UserManagement, SiteVisitorTrack
)

# Global Monkey-Patch to automatically set 'created_by' on all models when created via Admin
original_save_model = admin.ModelAdmin.save_model
def custom_save_model(self, request, obj, form, change):
    if not change and hasattr(obj, 'created_by') and not obj.created_by:
        obj.created_by = request.user.username
    original_save_model(self, request, obj, form, change)
admin.ModelAdmin.save_model = custom_save_model

original_save_formset = admin.ModelAdmin.save_formset
def custom_save_formset(self, request, form, formset, change):
    instances = formset.save(commit=False)
    for instance in instances:
        if not instance.pk and hasattr(instance, 'created_by') and not getattr(instance, 'created_by', None):
            instance.created_by = request.user.username
        instance.save()
    for obj in formset.deleted_objects:
        obj.delete()
    formset.save_m2m()
admin.ModelAdmin.save_formset = custom_save_formset

original_nested_save_model = NestedModelAdmin.save_model
def custom_nested_save_model(self, request, obj, form, change):
    if not change and hasattr(obj, 'created_by') and not obj.created_by:
        obj.created_by = request.user.username
    original_nested_save_model(self, request, obj, form, change)
NestedModelAdmin.save_model = custom_nested_save_model

original_nested_save_formset = NestedModelAdmin.save_formset
def custom_nested_save_formset(self, request, form, formset, change):
    instances = formset.save(commit=False)
    for instance in instances:
        if not instance.pk and hasattr(instance, 'created_by') and not getattr(instance, 'created_by', None):
            instance.created_by = request.user.username
        instance.save()
    for obj in formset.deleted_objects:
        obj.delete()
    formset.save_m2m()
NestedModelAdmin.save_formset = custom_nested_save_formset

# Base Admin for settings (Singleton behavior)
class BaseSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if self.model.objects.exists():
            obj = self.model.objects.first()
            return HttpResponseRedirect(reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change', args=[obj.pk]))
        return super().changelist_view(request, extra_context=extra_context)

# 0. Navbar Menus Inline
class NavbarMenuInline(admin.TabularInline):
    model = NavbarMenu
    extra = 1
    fields = ['name', 'section_id', 'order']

# 1. Navbar Content
@admin.register(NavbarSettings)
class NavbarSettingsAdmin(BaseSettingsAdmin):
    fields = ['site_title', 'nav_name', 'logo', 'favicon']
    inlines = [NavbarMenuInline]

# 2. Hero Section Content
@admin.register(HeroMainSettings)
class HeroMainSettingsAdmin(BaseSettingsAdmin):
    fields = ['hero_greeting', 'hero_name', 'hero_description', 'hero_profile_image', 'resume_file']

@admin.register(HeroSocialSettings)
class HeroSocialSettingsAdmin(BaseSettingsAdmin):
    fields = [
        'linkedin_url', 'linkedin_logo',
        'facebook_url', 'facebook_logo',
        'github_url', 'github_logo',
        'instagram_url', 'instagram_logo',
        'x_url', 'x_logo'
    ]

# 3. About Me Content
@admin.register(AboutSectionSettings)
class AboutSectionSettingsAdmin(BaseSettingsAdmin):
    fields = ['about_title', 'about_description', 'about_who_am_i']

@admin.register(AcademicBackground)
class AcademicBackgroundAdmin(admin.ModelAdmin):
    list_display = ['institution_name', 'degree_name', 'order']
    list_editable = ['order']
    exclude = ['settings', 'created_by']


# 5. Technical Skills
class SkillItemInline(admin.TabularInline):
    model = SkillItem
    extra = 0
    fields = ('name', 'order')
    exclude = ['created_by']

@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)
    inlines = [SkillItemInline]
    exclude = ['settings', 'created_by']
    change_list_template = "admin/core/skillcategory/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST':
            if 'update_technical_skills_description' in request.POST:
                description = request.POST.get('technical_skills_description')
                settings = HomeSettings.load()
                settings.technical_skills_description = description
                settings.save()
                from django.contrib import messages
                messages.success(request, "Technical Skills description updated successfully.")
                return HttpResponseRedirect(request.get_full_path())

            if 'add_technical_skill' in request.POST:
                name = request.POST.get('category_name')
                order = request.POST.get('category_order', 0)
                if name:
                    SkillCategory.objects.create(
                        name=name,
                        order=order,
                        settings=HomeSettings.load()
                    )
                    from django.contrib import messages
                    messages.success(request, f"Technical Skill '{name}' added successfully.")
                return HttpResponseRedirect(request.get_full_path())
            
            if 'run_skill_card_action' in request.POST:
                action = request.POST.get('skill_card_action')
                selected_ids = request.POST.getlist('_selected_skill_card')
                if action == 'delete_selected' and selected_ids:
                    count = Skill.objects.filter(id__in=selected_ids).delete()[0]
                    from django.contrib import messages
                    messages.success(request, f"Successfully deleted {count} skill cards.")
                return HttpResponseRedirect(request.get_full_path())

            if 'save_skill_cards_order' in request.POST:
                updated_count = 0
                for key, value in request.POST.items():
                    if key.startswith('order_'):
                        try:
                            card_id = key.split('_')[1]
                            order_val = int(value)
                            Skill.objects.filter(id=card_id).update(order=order_val)
                            updated_count += 1
                        except (ValueError, IndexError):
                            continue
                if updated_count > 0:
                    from django.contrib import messages
                    messages.success(request, f"Successfully updated order for {updated_count} skill cards.")
                return HttpResponseRedirect(request.get_full_path())

            if 'add_skill_card' in request.POST:
                name = request.POST.get('skill_name')
                order = request.POST.get('skill_order', 0)
                image = request.FILES.get('skill_image')
                if name and image:
                    Skill.objects.create(
                        name=name,
                        image=image,
                        order=order,
                        settings=HomeSettings.load()
                    )
                    from django.contrib import messages
                    messages.success(request, f"Skill Card '{name}' added successfully.")
                else:
                    from django.contrib import messages
                    messages.error(request, "Please provide both Name and Image for the Skill Card.")
                return HttpResponseRedirect(request.get_full_path())

        extra_context = extra_context or {}
        settings = HomeSettings.load()
        extra_context['technical_skills_description'] = settings.technical_skills_description
        extra_context['skill_cards'] = Skill.objects.all().order_by('order')
        extra_context['skill_cards_count'] = extra_context['skill_cards'].count()
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)
    fields = ('name', 'image', 'order')
    exclude = ['settings', 'created_by']

    def has_module_permission(self, request):
        return False

# 4. My Experience Content
@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'designation', 'start_date', 'end_description')
    list_filter = ('is_current', 'start_date')
    search_fields = ('company_name', 'designation')
    exclude = ['created_by']

    def end_description(self, obj):
        return "Present" if obj.is_current or not obj.end_date else obj.end_date
    end_description.short_description = "End Date"

# 5. My Expertise Content
@admin.register(ProfessionalTrainingModel)
class ProfessionalTrainingAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'organization_name', 'mode', 'order']
    list_editable = ['order']
    list_filter = ['mode']
    exclude = ['category', 'settings', 'created_by']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(category='TRAINING')

    def save_model(self, request, obj, form, change):
        obj.category = 'TRAINING'
        super().save_model(request, obj, form, change)

@admin.register(GlobalCertificationModel)
class GlobalCertificationAdmin(admin.ModelAdmin):
    list_display = ['course_name', 'organization_name', 'mode', 'order']
    list_editable = ['order']
    list_filter = ['mode']
    exclude = ['category', 'settings', 'created_by']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(category='CERTIFICATION')

    def save_model(self, request, obj, form, change):
        obj.category = 'CERTIFICATION'
        super().save_model(request, obj, form, change)

# 6. Featured Projects
class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 0
    exclude = ['created_by']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'tech_stack', 'created_at')
    inlines = [ProjectImageInline]
    exclude = ['settings', 'created_by']
    change_list_template = "admin/core/project/change_list.html"
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'image')
        }),
        ('Technologies & Links', {
            'fields': ('tech_stack', 'live_link', 'repo_link'),
            'description': "Enter technologies separated by commas."
        }),
    )

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'update_projects_description' in request.POST:
            description = request.POST.get('projects_description')
            settings = HomeSettings.load()
            settings.projects_description = description
            settings.save()
            from django.contrib import messages
            messages.success(request, "Projects description updated successfully.")
            return HttpResponseRedirect(request.get_full_path())

        extra_context = extra_context or {}
        settings = HomeSettings.load()
        extra_context['projects_description'] = settings.projects_description
        return super().changelist_view(request, extra_context=extra_context)

# 7. My Services
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon_class', 'order')
    list_editable = ('order',)
    exclude = ['settings', 'created_by']
    change_list_template = "admin/core/service/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'update_services_description' in request.POST:
            description = request.POST.get('services_description')
            settings = HomeSettings.load()
            settings.services_description = description
            settings.save()
            from django.contrib import messages
            messages.success(request, "Services description updated successfully.")
            return HttpResponseRedirect(request.get_full_path())

        extra_context = extra_context or {}
        settings = HomeSettings.load()
        extra_context['services_description'] = settings.services_description
        return super().changelist_view(request, extra_context=extra_context)

# 8. My Blog Content

class BlogPostImageInline(admin.TabularInline):
    model = BlogPostImage
    extra = 1
    fields = ['image', 'caption', 'order']
    exclude = ['created_by']
    sortable_field_name = "order"

# Blog Analytics Inlines (Dashboard & Metrics)
class BlogCommentInline(admin.TabularInline):
    model = BlogComment
    extra = 0
    readonly_fields = ['user', 'content', 'created_at']
    fields = ['user', 'content', 'created_at']
    can_delete = False
    verbose_name = "Comment"
    verbose_name_plural = "Comments"

class BlogReactionInline(admin.TabularInline):
    model = BlogReaction
    extra = 0
    readonly_fields = ['user', 'reaction', 'created_at']
    fields = ['user', 'reaction', 'created_at']
    can_delete = False
    verbose_name = "Reaction"
    verbose_name_plural = "Reactions"

class BlogViewTrackInline(admin.TabularInline):
    model = BlogViewTrack
    extra = 0
    readonly_fields = ['display_user_info', 'contact_number', 'ip_address', 'browsing_source', 'created_at']
    fields = ['display_user_info', 'contact_number', 'ip_address', 'browsing_source', 'created_at']
    can_delete = False
    verbose_name = "View Track"
    verbose_name_plural = "View Tracks"

    def display_user_info(self, obj):
        if obj.user:
            name = obj.user.get_full_name() or obj.user.username
            return f"{name}, {obj.user.email}"
        return "Anonymous Visitor"
    display_user_info.short_description = "Visitor Details (Name, Email)"

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    change_list_template = "admin/core/blogpost/change_list.html"
    list_display = (
        'title', 'category', 'total_views', 'total_likes', 
        'total_dislikes', 'total_comments', 'created_at'
    )
    search_fields = ('title', 'content', 'category')
    prepopulated_fields = {'slug': ('title',)}
    list_filter = ('category', 'created_at')
    
    # Combined Inlines: Post Editing + Analytics
    inlines = [
        BlogPostImageInline,
        BlogViewTrackInline,
        BlogReactionInline,
        BlogCommentInline
    ]
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'content')
        }),
        ('Statistics', {
            'fields': ('views',),
            'classes': ('collapse',),
            'description': "Quick stats counter. See detailed View Tracks below."
        }),
    )
    exclude = ['settings', 'created_by']

    class Media:
        js = ('js/blog_admin.js',)
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',)
        }

    def get_queryset(self, request):
        from django.db.models import Count, Q
        qs = super().get_queryset(request)
        return qs.annotate(
            total_likes=Count('reactions', filter=Q(reactions__reaction='like'), distinct=True),
            total_dislikes=Count('reactions', filter=Q(reactions__reaction='dislike'), distinct=True),
            total_comments=Count('comments', distinct=True),
            total_view_tracks=Count('view_tracks', distinct=True)
        )

    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'update_blog_description' in request.POST:
            description = request.POST.get('blog_section_description')
            settings = HomeSettings.load()
            settings.blog_section_description = description
            settings.save()
            from django.contrib import messages
            messages.success(request, "Blog section description updated successfully.")
            return HttpResponseRedirect(request.get_full_path())

        extra_context = extra_context or {}
        settings = HomeSettings.load()
        extra_context['blog_section_description'] = settings.blog_section_description
        extra_context['total_website_views'] = BlogViewTrack.objects.count()
        extra_context['total_likes'] = BlogReaction.objects.filter(reaction='like').count()
        extra_context['total_dislikes'] = BlogReaction.objects.filter(reaction='dislike').count()
        extra_context['total_comments'] = BlogComment.objects.count()
        return super().changelist_view(request, extra_context=extra_context)

    # Metric Columns for List View
    def total_views(self, obj):
        return obj.total_view_tracks
    total_views.short_description = "Views"
    total_views.admin_order_field = "total_view_tracks"

    def total_likes(self, obj):
        return obj.total_likes
    total_likes.short_description = "Likes"
    total_likes.admin_order_field = "total_likes"

    def total_dislikes(self, obj):
        return obj.total_dislikes
    total_dislikes.short_description = "Dislikes"
    total_dislikes.admin_order_field = "total_dislikes"

    def total_comments(self, obj):
        return obj.total_comments
    total_comments.short_description = "Comments"
    total_comments.admin_order_field = "total_comments"

# 9. Contact
@admin.register(ContactSectionSettings)
class ContactSectionSettingsAdmin(BaseSettingsAdmin):
    fields = ['contact_heading', 'contact_sub_heading', 'contact_text'] 

# 10. Footer Content
@admin.register(FooterSettings)
class FooterSettingsAdmin(BaseSettingsAdmin):
    fields = ['footer_copyright']

# User Submissions
@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ['formatted_name', 'formatted_service', 'booking_date', 'formatted_date', 'formatted_time', 'conflict_check', 'booking_status']
    list_filter = ['status', 'service', 'date_from', 'created_at']
    readonly_fields = ['created_at']
    exclude = ['created_by']
    
    def formatted_name(self, obj):
        return format_html('<span style="white-space: nowrap;">{}</span>', obj.name)
    formatted_name.short_description = "Name"

    def formatted_service(self, obj):
        return format_html('<div style="white-space: normal; min-width: 150px;">{}</div>', obj.service)
    formatted_service.short_description = "Service"

    def booking_date(self, obj):
        return obj.created_at.strftime('%d %b %Y, %I:%M %p')
    booking_date.short_description = "Booking Date"
    booking_date.admin_order_field = 'created_at'
    
    def formatted_date(self, obj):
        if obj.date_from == obj.date_to:
            return obj.date_from.strftime('%d-%b-%y')
        return f"{obj.date_from.strftime('%d-%b-%y')} - {obj.date_to.strftime('%d-%b-%y')}"
    formatted_date.short_description = "Date Range"
    formatted_date.admin_order_field = 'date_from'

    def formatted_time(self, obj):
        return f"{obj.time_from.strftime('%I:%M %p')} - {obj.time_to.strftime('%I:%M %p')}"
    formatted_time.short_description = "Time"
    formatted_time.admin_order_field = 'time_from'

    def conflict_check(self, obj):
        # Check for overlapping bookings in the same service at the same time
        conflicts = ServiceBooking.objects.filter(
            service=obj.service,
            date_from=obj.date_from,
            status__in=['pending', 'accepted']
        ).exclude(id=obj.id)
        
        # Check for time overlap
        overlap_count = 0
        for conflict in conflicts:
            if not (obj.time_to <= conflict.time_from or obj.time_from >= conflict.time_to):
                overlap_count += 1
        
        if overlap_count > 0:
            total_at_slot = overlap_count + 1
            return format_html('<span style="color: #ff4757; font-weight: bold; background: rgba(255,71,87,0.1); padding: 4px 8px; border-radius: 4px;">Conflict ({} Requests)</span>', total_at_slot)
        return format_html('<span style="color: #2ed573; font-weight: 500;">{}</span>', "No Conflict")
    conflict_check.short_description = "Conflict Tracking"

    def booking_status(self, obj):
        if obj.status == 'pending':
            accept_url = reverse('admin:accept-booking', args=[obj.pk])
            cancel_url = reverse('admin:cancel-booking', args=[obj.pk])
            return format_html(
                '<div style="display: flex; gap: 4px;">'
                '<a class="status-btn" href="{}" style="background-color: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-weight: 600; font-size: 11px; box-shadow: 0 1px 2px rgba(40,167,69,0.3);"><i class="fas fa-check"></i> Accept</a>'
                '<a class="status-btn" href="{}" style="background-color: #dc3545; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-weight: 600; font-size: 11px; box-shadow: 0 1px 2px rgba(220,53,69,0.3);"><i class="fas fa-times"></i> Cancel</a>'
                '</div>',
                accept_url, cancel_url
            )
        
        # Color schemes for tags
        styles = {
            'accepted': 'background: #28a745; color: white;',
            'cancelled': 'background: #dc3545; color: white;',
        }
        icons = {
            'accepted': 'fa-check-circle',
            'cancelled': 'fa-times-circle',
        }
        
        return format_html(
            '<span style="{} padding: 4px 10px; border-radius: 12px; font-weight: 700; font-size: 10px; text-transform: uppercase; display: inline-flex; align-items: center; gap: 4px;">'
            '<i class="fas {}"></i> {}</span>',
            styles.get(obj.status, ''),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    booking_status.short_description = "Status & Actions"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('accept/<int:booking_id>/', self.admin_site.admin_view(self.accept_booking), name='accept-booking'),
            path('cancel/<int:booking_id>/', self.admin_site.admin_view(self.cancel_booking), name='cancel-booking'),
        ]
        return custom_urls + urls

    def accept_booking(self, request, booking_id):
        booking = get_object_or_404(ServiceBooking, id=booking_id)
        booking.status = 'accepted'
        booking.save()
        
        # Send confirmation email
        from .utils import send_portfolio_email
        if booking.date_from == booking.date_to:
            booking_date = booking.date_from.strftime('%d-%b-%y')
        else:
            booking_date = f"{booking.date_from.strftime('%d-%b-%y')} to {booking.date_to.strftime('%d-%b-%y')}"
        
        booking_time = f"{booking.time_from.strftime('%I:%M %p')} to {booking.time_to.strftime('%I:%M %p')}"
        
        subject = f"Booking Approved: {booking.service.title}"
        body = f"Hello {booking.name},\n\nYour booking for '{booking.service.title}' on {booking_date} at {booking_time} has been APPROVED.\n\nWe look forward to seeing you.\n\nBest regards,\nPortfolio Team"
        send_portfolio_email(subject, body, to_email=booking.email)
        
        self.message_user(request, f"Booking for {booking.name} accepted and email sent.")
        return HttpResponseRedirect(reverse('admin:core_servicebooking_changelist'))

    def cancel_booking(self, request, booking_id):
        booking = get_object_or_404(ServiceBooking, id=booking_id)
        booking.status = 'cancelled'
        booking.save()
        
        # Send cancellation email
        from .utils import send_portfolio_email
        subject = f"Booking Update: {booking.service.title}"
        body = f"Hello {booking.name},\n\nWe regret to inform you that the requested session for '{booking.service.title}' is not available at the requested time.\n\nWe encourage you to apply again for another time slot in the future.\n\nBest regards,\nPortfolio Team"
        send_portfolio_email(subject, body, to_email=booking.email)
        
        self.message_user(request, f"Booking for {booking.name} cancelled and email sent.")
        return HttpResponseRedirect(reverse('admin:core_servicebooking_changelist'))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        services = Service.objects.all()
        summary_data = []
        
        total_all = ServiceBooking.objects.count()
        accepted_all = ServiceBooking.objects.filter(status='accepted').count()
        pending_all = ServiceBooking.objects.filter(status='pending').count()
        cancelled_all = ServiceBooking.objects.filter(status='cancelled').count()
        
        summary_data.append({
            'name': 'Summary',
            'total': f"{total_all:02d}",
            'accepted': f"{accepted_all:02d}",
            'pending': f"{pending_all:02d}",
            'cancelled': f"{cancelled_all:02d}",
            'is_summary': True
        })
        
        for service in services:
            total = service.bookings.count()
            accepted = service.bookings.filter(status='accepted').count()
            pending = service.bookings.filter(status='pending').count()
            cancelled = service.bookings.filter(status='cancelled').count()
            
            summary_data.append({
                'name': service.title,
                'total': f"{total:02d}",
                'accepted': f"{accepted:02d}",
                'pending': f"{pending:02d}",
                'cancelled': f"{cancelled:02d}",
                'is_summary': False
            })
            
        extra_context['summary_data'] = summary_data
        return super().changelist_view(request, extra_context=extra_context)

    change_list_template = "admin/core/servicebooking/change_list.html"
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Booking Details', {
            'fields': ('service', 'status', 'additional_message')
        }),
        ('Date Range', {
            'fields': (('date_from', 'date_to'),)
        }),
        ('Time Range', {
            'fields': (('time_from', 'time_to'),)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(SiteVisitorTrack)
class SiteVisitorTrackAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/sitevisitortrack/change_list.html'
    list_display = ['get_visitor', 'get_path', 'browsing_source', 'visited_at', 'last_activity', 'get_duration']
    list_filter = ['visited_at', 'last_activity', 'path']
    search_fields = ['name', 'email', 'ip_address', 'user_agent', 'browsing_source', 'path']
    readonly_fields = [
        'user', 'ip_address', 'user_agent', 'browsing_source', 'path', 
        'session_key', 'name', 'email', 'contact_number', 'visited_at', 'last_activity'
    ]
    
    def get_visitor(self, obj):
        name = obj.name or "Anonymous"
        email = f" ({obj.email})" if obj.email else ""
        return format_html('<b>{}</b><br><small>{}</small>', f"{name}{email}", obj.ip_address)
    get_visitor.short_description = 'Visitor Details'
    
    def get_path(self, obj):
        return format_html('<code style="color: #2980b9;">{}</code>', obj.path)
    get_path.short_description = 'Visited Path'

    def get_duration(self, obj):
        return obj.duration
    get_duration.short_description = 'Duration'

    def changelist_view(self, request, extra_context=None):
        from django.db.models import Count
        from django.utils import timezone
        
        # Summary Statistics
        total_sessions = SiteVisitorTrack.objects.count()
        unique_ips = SiteVisitorTrack.objects.values('ip_address').distinct().count()
        today = timezone.now().date()
        today_visits = SiteVisitorTrack.objects.filter(visited_at__date=today).count()
        
        # Top 5 Visited Pages
        top_pages = SiteVisitorTrack.objects.values('path').annotate(
            count=Count('path')).order_by('-count')[:5]
            
        extra_context = extra_context or {}
        extra_context.update({
            'analytics': {
                'total_sessions': total_sessions,
                'unique_visitors': unique_ips,
                'today_visits': today_visits,
                'top_pages': top_pages,
            },
            'title': "Site Viewer Tracking & Analytics"
        })
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'created_at']
    readonly_fields = ['created_at']
    exclude = ['created_by']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'profession', 'location', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating']
    search_fields = ['name', 'comment']
    list_editable = ['is_approved']
    exclude = ['created_by']
    
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

# 12. User Management
from django.contrib.auth.admin import UserAdmin

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Info'
    fk_name = 'user'
    
class UserBlogCommentInline(admin.TabularInline):
    model = BlogComment
    fk_name = 'user'
    extra = 0
    readonly_fields = ['post', 'content', 'created_at']
    fields = ['post', 'content', 'created_at']
    can_delete = True
    verbose_name = "User's Comment"
    verbose_name_plural = "User's Comments"

class UserBlogReactionInline(admin.TabularInline):
    model = BlogReaction
    fk_name = 'user'
    extra = 0
    readonly_fields = ['post', 'reaction', 'created_at']
    fields = ['post', 'reaction', 'created_at']
    can_delete = True
    verbose_name = "User's Reaction"
    verbose_name_plural = "User's Reactions"

class UserBlogViewTrackInline(admin.TabularInline):
    model = BlogViewTrack
    fk_name = 'user'
    extra = 0
    readonly_fields = ['post', 'ip_address', 'user_agent', 'browsing_source', 'created_at']
    fields = ['post', 'ip_address', 'user_agent', 'browsing_source', 'created_at']
    can_delete = False
    verbose_name = "User's View Track"
    verbose_name_plural = "User's View Tracks"

@admin.register(UserManagement)
class UserManagementAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    inlines = [UserProfileInline, UserBlogCommentInline, UserBlogReactionInline, UserBlogViewTrackInline]

    def has_add_permission(self, request):
        return False
        
    def get_fieldsets(self, request, obj=None):
        return (
            (None, {'fields': ('username', 'password')}),
            ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
            ('Account Status', {'fields': ('is_active',)}),
            ('Important dates', {'fields': ('last_login', 'date_joined')}),
        )

# Unregister unused/helper
# SkillCategory is registered above for 'Expertise' section. I will check.
# Yes, it is.

# Cleanup - Unregister Group and User (not needed for single-user portfolio)
try:
    from django.contrib.auth.models import Group, User
    admin.site.unregister(Group)
    admin.site.unregister(User)
except:
    pass
