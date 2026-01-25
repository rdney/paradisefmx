"""Custom template tags for i18n."""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context, language):
    """
    Get the current URL translated to the given language.
    Strips the current language prefix and adds the new one if needed.
    """
    # Get the view object which has the HTTP request
    view = context.get('view')
    if view and hasattr(view, 'request'):
        path = view.request.get_full_path()
    else:
        return '/'

    # Remove query string for cleaner language switch
    if '?' in path:
        path = path.split('?')[0]

    # Strip existing language prefix (/en/, /nl/, etc.)
    # Our setup uses prefix_default_language=False, so Dutch has no prefix
    if path.startswith('/en/'):
        path = path[3:]  # Remove /en prefix, keep the /
    elif path.startswith('/nl/'):
        path = path[3:]  # Remove /nl prefix, keep the /

    # Add new language prefix if not default (Dutch)
    if language == 'en':
        return '/en' + path
    else:
        return path
