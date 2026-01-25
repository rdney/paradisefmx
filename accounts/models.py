from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


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
