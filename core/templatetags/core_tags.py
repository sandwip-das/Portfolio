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
    
    # We skip the first 2 images because they are shown at the top
    interleave_images = images[2:] if len(images) > 2 else []
    
    result = []
    
    for i, para in enumerate(paras):
        result.append(para)
        
        # If we have an image for this paragraph, inject it
        if i < len(interleave_images):
            img = interleave_images[i]
            img_url = img.image.url if img.image else ''
            caption_text = img.caption if img.caption else getattr(post, 'title', '')
            
            caption_html = ''
            if img.caption:
                caption_html = f'<p class="text-center text-sm text-gray-400 p-3 bg-white/5 m-0 border-t border-white/10">{img.caption}</p>'
                
            img_html = f'''
            <div class="flex justify-center my-10">
                <div class="rounded-2xl overflow-hidden border border-white/10 shadow-xl w-full md:w-1/4 hover:shadow-[#2ecc71]/20 transition-shadow">
                    <img src="{img_url}" alt="{caption_text}" class="w-full h-auto object-cover">
                    {caption_html}
                </div>
            </div>
            '''
            result.append(img_html)
            
    # Append any remaining images at the very end
    if len(interleave_images) > len(paras):
        for img in interleave_images[len(paras):]:
            img_url = img.image.url if img.image else ''
            caption_text = img.caption if img.caption else getattr(post, 'title', '')
            
            caption_html = ''
            if img.caption:
                caption_html = f'<p class="text-center text-sm text-gray-400 p-3 bg-white/5 m-0 border-t border-white/10">{img.caption}</p>'
                
            img_html = f'''
            <div class="flex justify-center my-10">
                <div class="rounded-2xl overflow-hidden border border-white/10 shadow-xl w-full md:w-1/4 hover:shadow-[#2ecc71]/20 transition-shadow">
                    <img src="{img_url}" alt="{caption_text}" class="w-full h-auto object-cover">
                    {caption_html}
                </div>
            </div>
            '''
            result.append(img_html)

    return mark_safe('\n'.join(result))
