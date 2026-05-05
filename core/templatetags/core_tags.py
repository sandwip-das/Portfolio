from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='tech_badges')
def tech_badges(tech_stack_string):
    """
    Takes a comma-separated string like "Django, Python, React"
    and returns rendered HTML badges.

    Usage in template:
        {{ project.tech_stack|tech_badges }}

    This eliminates the need for {% for %} loops in templates,
    preventing line-wrapping issues with {{ tech }} variables.
    """
    if not tech_stack_string:
        return mark_safe(
            '<span class="text-xs text-gray-500">'
            'No tech stack listed</span>'
        )

    techs = [t.strip() for t in tech_stack_string.split(',') if t.strip()]

    if not techs:
        return mark_safe(
            '<span class="text-xs text-gray-500">'
            'No tech stack listed</span>'
        )

    badges = []
    for tech in techs:
        safe_name = escape(tech)
        badge = (
            f'<span class="text-xs font-semibold text-primary '
            f'bg-primary/10 px-3 py-1 rounded-full border '
            f'border-primary/20">{safe_name}</span>'
        )
        badges.append(badge)

    return mark_safe(' '.join(badges))


@register.filter(name='default_text')
def default_text(value, default=""):
    """
    Safe default filter that works on any field.
    Returns the default if value is empty/None.

    Usage:
        {{ settings.technical_skills_description|default_text:"Fallback text here" }}
    """
    if value:
        return value
    return default


@register.filter(name='paragraphs_with_divider')
def paragraphs_with_divider(text):
    """
    Splits text into paragraphs (by blank lines) and renders them
    with a narrow white/gray divider between each paragraph.

    Usage in template:
        {{ settings.about_description|paragraphs_with_divider }}

    Input (from Django admin textarea):
        "First paragraph here.

        Second paragraph here.

        Third paragraph here."

    Output: Styled <p> tags with thin divider lines between them.
    """
    if not text:
        return ''

    # Split by double newlines (paragraph breaks)
    # Also handle \r\n line endings
    raw = text.replace('\r\n', '\n')
    paragraphs = [p.strip() for p in raw.split('\n\n') if p.strip()]

    # If no double-newlines found, try single newlines
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in raw.split('\n') if p.strip()]

    if not paragraphs:
        return ''

    divider = (
        '<div class="my-3">'
        '<div class="w-full h-px bg-gradient-to-r from-transparent via-white/30 to-transparent"></div>'
        '</div>'
    )

    parts = []
    for i, para in enumerate(paragraphs):
        safe_text = escape(para)
        parts.append(
            f'<p class="text-white leading-relaxed text-base">{safe_text}</p>'
        )
        if i < len(paragraphs) - 1:
            parts.append(divider)

    return mark_safe('\n'.join(parts))


@register.filter(name='get_at_index')
def get_at_index(list_data, index):
    try:
        return list_data[index]
    except (IndexError, TypeError):
        return None


@register.filter(name='paragraphs_as_list')
def paragraphs_as_list(text):
    if not text:
        return []

    # If it's HTML (RichText), split by closing </p> tag
    if '</p>' in text:
        import re
        # This is a bit naive but works for standard CKEditor output
        paras = re.findall(r'<p>.*?</p>', text, re.DOTALL)
        if not paras:
            return [text]
        return paras
    
    # Text fallback
    raw = text.replace('\r\n', '\n')
    paragraphs = [p.strip() for p in raw.split('\n\n') if p.strip()]
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in raw.split('\n') if p.strip()]
    return paragraphs

@register.filter(name='render_interleaved_content')
def render_interleaved_content(post):
    if not post or not getattr(post, 'content', None):
        return ""
        
    text = post.content
    if '</p>' in text:
        import re
        paras = re.findall(r'<p>.*?</p>', text, re.DOTALL)
        if not paras:
            paras = [text]
    else:
        raw = text.replace('\r\n', '\n')
        paras = [p.strip() for p in raw.split('\n\n') if p.strip()]
        if len(paras) <= 1:
            paras = [p.strip() for p in raw.split('\n') if p.strip()]
        paras = [f'<p>{p}</p>' for p in paras]
        
    images = list(post.images.all())
    # Only skip the first image (feature image)
    content_images = images[1:] if len(images) > 1 else []
    
    # Group images by their order
    from collections import defaultdict
    groups_dict = defaultdict(list)
    for img in content_images:
        groups_dict[img.order].append(img)
    
    # Sort orders to ensure they appear correctly
    sorted_orders = sorted(groups_dict.keys())
    image_groups = [groups_dict[order] for order in sorted_orders]
    
    result = []
    
    for i, para in enumerate(paras):
        result.append(para)
        
        # If we have an image group for this index, inject it
        if i < len(image_groups):
            group = image_groups[i]
            
            # Determine width based on number of images in group
            # If 1 image: w-full or md:w-3/4
            # If 2+ images: flex-row with shared width
            
            group_html = '<div class="flex flex-wrap justify-center gap-4 my-2">'
            for img in group:
                img_url = img.image.url if img.image else ''
                caption_text = img.caption if img.caption else ''
                
                # Determine individual image container width - Set to 1/4 as requested
                width_class = "w-full md:w-1/4"
                
                caption_html = ''
                if caption_text:
                    caption_html = f'<p class="mt-2 text-center text-sm text-gray-300 font-medium italic">{caption_text}</p>'
                
                img_html = f'''
                <div class="{width_class} group/img">
                    <div class="aspect-video rounded-2xl overflow-hidden border border-white/10 shadow-lg hover:shadow-[#2ecc71]/20 transition-all duration-300">
                        <img src="{img_url}" alt="{caption_text or post.title}" class="w-full h-full object-cover transform group-hover/img:scale-[1.05] transition-transform duration-500">
                    </div>
                    {caption_html}
                </div>
                '''
                group_html += img_html
            
            group_html += '</div>'
            result.append(group_html)
            
    # Append any remaining image groups at the very end
    if len(image_groups) > len(paras):
        for group in image_groups[len(paras):]:
            group_html = '<div class="flex flex-wrap justify-center gap-4 my-2">'
            for img in group:
                img_url = img.image.url if img.image else ''
                caption_text = img.caption if img.caption else ''
                
                width_class = "w-full md:w-1/4"
                
                caption_html = ''
                if caption_text:
                    caption_html = f'<p class="mt-2 text-center text-sm text-gray-300 font-medium italic">{caption_text}</p>'
                
                img_html = f'''
                <div class="{width_class} group/img">
                    <div class="aspect-video rounded-2xl overflow-hidden border border-white/10 shadow-lg hover:shadow-[#2ecc71]/20 transition-all duration-300">
                        <img src="{img_url}" alt="{caption_text or post.title}" class="w-full h-full object-cover transform group-hover/img:scale-[1.05] transition-transform duration-500">
                    </div>
                    {caption_html}
                </div>
                '''
                group_html += img_html
            group_html += '</div>'
            result.append(group_html)

    return mark_safe('\n'.join(result))
@register.filter(name='smart_url')
def smart_url(file_field):
    """
    A robust way to get the Cloudinary URL.
    Detects and fixes double-prefixing (e.g., domain/domain/path).
    """
    if not file_field:
        return ""
        
    try:
        url = file_field.url
        cloud_name = "dghadnok8"
        
        # If the domain appears more than once, it's double-prefixed
        if url.count("res.cloudinary.com") > 1:
            # Take everything after the LAST occurrence of the cloud name
            if f"{cloud_name}/" in url:
                path = url.split(f"{cloud_name}/")[-1]
                return f"https://res.cloudinary.com/{cloud_name}/{path}"
        
        return url
    except Exception:
        return ""

@register.inclusion_tag('partials/tags/profile_image.html')
def render_profile_image(user, css_class="h-8 w-8"):
    """
    Renders a user's profile image or their initials if no image is set.
    Centralizes logic to avoid repetition across navbar and profile pages.
    """
    profile = getattr(user, 'profile', None)
    has_image = False
    image_url = ""
    
    if profile and profile.profile_picture and profile.profile_picture.name != 'default_profile.png':
        has_image = True
        # Use our existing smart_url logic internally
        image_url = smart_url(profile.profile_picture)
        
    return {
        'user': user,
        'has_image': has_image,
        'image_url': image_url,
        'css_class': css_class
    }
