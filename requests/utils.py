"""Utility functions for the requests app."""
import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.translation import gettext as _

User = get_user_model()

# Pattern to match @username (alphanumeric and underscores)
MENTION_PATTERN = re.compile(r'@(\w+)')


def extract_mentions(text):
    """Extract @usernames from text and return matching User objects."""
    if not text:
        return []

    usernames = MENTION_PATTERN.findall(text)
    if not usernames:
        return []

    return list(User.objects.filter(username__in=usernames))


def send_mention_notifications(worklog, mentioned_users, request_url=''):
    """Send email notifications to mentioned users."""
    if not mentioned_users:
        return

    repair_request = worklog.repair_request
    author_name = worklog.author.get_full_name() or worklog.author.username if worklog.author else _('Iemand')

    subject = _('Je bent genoemd in verzoek #%(id)s') % {'id': repair_request.id}

    for user in mentioned_users:
        if not user.email:
            continue

        message = _(
            'Hallo %(name)s,\n\n'
            '%(author)s heeft je genoemd in een notitie bij verzoek #%(id)s: %(title)s\n\n'
            'Notitie:\n%(note)s\n\n'
            '%(url)s'
        ) % {
            'name': user.get_full_name() or user.username,
            'author': author_name,
            'id': repair_request.id,
            'title': repair_request.title,
            'note': worklog.note,
            'url': request_url,
        }

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception:
            pass  # Don't fail if email fails


def highlight_mentions(text):
    """Convert @username to highlighted HTML."""
    if not text:
        return text

    def replace_mention(match):
        username = match.group(1)
        return f'<strong class="text-primary">@{username}</strong>'

    return MENTION_PATTERN.sub(replace_mention, text)
