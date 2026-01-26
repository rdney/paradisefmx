from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def user_display(user):
    """Display user name with their primary group."""
    if not user:
        return ""

    name = user.get_full_name() or user.username
    group = user.groups.first()

    if group:
        return format_html('{} <span class="badge bg-light text-muted">{}</span>', name, group.name)
    return name


@register.filter
def user_display_plain(user):
    """Display user name with group (plain text, no HTML)."""
    if not user:
        return ""

    name = user.get_full_name() or user.username
    group = user.groups.first()

    if group:
        return f"{name} ({group.name})"
    return name
