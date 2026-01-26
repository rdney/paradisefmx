import secrets

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def generate_token():
    return secrets.token_urlsafe(32)


class Invitation(models.Model):
    """Invitation to join the application."""

    class Status(models.TextChoices):
        PENDING = 'pending', _('Uitstaand')
        ACCEPTED = 'accepted', _('Geaccepteerd')
        EXPIRED = 'expired', _('Verlopen')
        CANCELLED = 'cancelled', _('Geannuleerd')

    email = models.EmailField(_('e-mailadres'))
    token = models.CharField(_('token'), max_length=64, unique=True, default=generate_token)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations',
        verbose_name=_('uitgenodigd door')
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('groep'),
        help_text=_('Groep waar de gebruiker aan wordt toegevoegd')
    )
    message = models.TextField(_('persoonlijk bericht'), blank=True)
    created_at = models.DateTimeField(_('aangemaakt'), auto_now_add=True)
    accepted_at = models.DateTimeField(_('geaccepteerd op'), null=True, blank=True)
    accepted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitation',
        verbose_name=_('geaccepteerd door')
    )

    class Meta:
        verbose_name = _('uitnodiging')
        verbose_name_plural = _('uitnodigingen')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_status_display()})"

    @property
    def is_valid(self):
        """Check if invitation can still be accepted."""
        if self.status != self.Status.PENDING:
            return False
        # Expire after 7 days
        expiry = self.created_at + timezone.timedelta(days=7)
        if timezone.now() > expiry:
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status'])
            return False
        return True

    @property
    def expires_at(self):
        return self.created_at + timezone.timedelta(days=7)


class UserProfile(models.Model):
    """Extended user profile with additional settings."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('gebruiker')
    )
    must_change_password = models.BooleanField(
        _('wachtwoord wijzigen verplicht'),
        default=False,
        help_text=_('Gebruiker moet wachtwoord wijzigen bij volgende login')
    )

    class Meta:
        verbose_name = _('gebruikersprofiel')
        verbose_name_plural = _('gebruikersprofielen')

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile when user is created."""
    if created:
        UserProfile.objects.get_or_create(user=instance)
