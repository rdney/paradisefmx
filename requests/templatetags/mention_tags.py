"""Template tags for @mention handling."""
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

MENTION_PATTERN = re.compile(r'@(\w+)')


@register.filter(name='highlight_mentions')
def highlight_mentions(text):
    """Convert @username to highlighted HTML."""
    if not text:
        return text

    def replace_mention(match):
        username = match.group(1)
        return f'<strong class="text-primary">@{username}</strong>'

    result = MENTION_PATTERN.sub(replace_mention, str(text))
    return mark_safe(result)
