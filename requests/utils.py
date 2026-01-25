"""Utility functions for the requests app."""
import logging
import re
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.translation import gettext as _

User = get_user_model()
logger = logging.getLogger(__name__)

# Feature toggle for email notifications
ENABLE_EMAIL_NOTIFICATIONS = os.environ.get('ENABLE_EMAIL_NOTIFICATIONS', 'False').lower() in ('true', '1', 'yes')

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
    """Create in-app notifications and optionally send email to mentioned users."""
    from .models import Notification

    if not mentioned_users:
        return

    repair_request = worklog.repair_request
    author_name = worklog.author.get_full_name() or worklog.author.username if worklog.author else _('Iemand')

    for user in mentioned_users:
        # Always create in-app notification
        title = _('%(author)s heeft je genoemd') % {'author': author_name}
        message = _('In verzoek #%(id)s: %(title)s\n\n"%(note)s"') % {
            'id': repair_request.id,
            'title': repair_request.title,
            'note': worklog.note[:200] + '...' if len(worklog.note) > 200 else worklog.note,
        }

        Notification.objects.create(
            user=user,
            notification_type=Notification.NotificationType.MENTION,
            title=title,
            message=message,
            repair_request=repair_request,
        )
        logger.info(f'Notification created for {user.username}')

        # Send email only if enabled and user has email
        if ENABLE_EMAIL_NOTIFICATIONS and user.email:
            subject = _('Je bent genoemd in verzoek #%(id)s') % {'id': repair_request.id}
            email_message = _(
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
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                logger.info(f'Email notification sent to {user.email}')
            except Exception as e:
                logger.error(f'Failed to send email to {user.email}: {e}')


def highlight_mentions(text):
    """Convert @username to highlighted HTML."""
    if not text:
        return text

    def replace_mention(match):
        username = match.group(1)
        return f'<strong class="text-primary">@{username}</strong>'

    return MENTION_PATTERN.sub(replace_mention, text)
