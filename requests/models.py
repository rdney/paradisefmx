import os
import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import Asset, Location


class ActiveRequestManager(models.Manager):
    """Manager that excludes soft-deleted requests."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


def attachment_path(instance, filename):
    """Generate safe upload path for attachments."""
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"attachments/{instance.repair_request.id}/{safe_name}"


class RepairRequest(models.Model):
    """A repair or maintenance request (work order)."""

    # Managers
    objects = ActiveRequestManager()  # Default: excludes deleted
    all_objects = models.Manager()    # Includes deleted (for admin)

    class Priority(models.TextChoices):
        LOW = 'low', _('Laag')
        NORMAL = 'normal', _('Normaal')
        HIGH = 'high', _('Hoog')
        URGENT = 'urgent', _('Spoed')

    class Status(models.TextChoices):
        NEW = 'new', _('Nieuw')
        TRIAGED = 'triaged', _('Getriageerd')
        IN_PROGRESS = 'in_progress', _('Bezig')
        WAITING = 'waiting', _('Wacht')
        COMPLETED = 'completed', _('Gereed')
        CLOSED = 'closed', _('Gesloten')

    class ContactMethod(models.TextChoices):
        EMAIL = 'email', _('E-mail')
        PHONE = 'phone', _('Telefoon')

    class QuoteStatus(models.TextChoices):
        NONE = 'none', _('Geen')
        REQUESTED = 'requested', _('Aangevraagd')
        RECEIVED = 'received', _('Ontvangen')
        APPROVED = 'approved', _('Goedgekeurd')

    # Request details
    title = models.CharField(_('titel'), max_length=200)
    description = models.TextField(_('omschrijving'))
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        related_name='repair_requests',
        verbose_name=_('locatie')
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='repair_requests',
        verbose_name=_('object/installatie')
    )
    priority = models.CharField(
        _('prioriteit'),
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    status = models.CharField(
        _('status'),
        max_length=15,
        choices=Status.choices,
        default=Status.NEW
    )

    # Requester info
    requester_name = models.CharField(_('naam melder'), max_length=200)
    requester_email = models.EmailField(_('e-mailadres'), blank=True)
    requester_phone = models.CharField(_('telefoonnummer'), max_length=20, blank=True)
    preferred_contact_method = models.CharField(
        _('voorkeur contact'),
        max_length=10,
        choices=ContactMethod.choices,
        default=ContactMethod.EMAIL,
        blank=True
    )
    requester_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_requests',
        verbose_name=_('ingediend door')
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests',
        verbose_name=_('toegewezen aan')
    )
    triaged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triaged_requests',
        verbose_name=_('getriageerd door')
    )
    due_date = models.DateField(_('streefdatum'), null=True, blank=True)

    # Resolution
    resolution_summary = models.TextField(_('oplossing'), blank=True)
    estimated_cost = models.DecimalField(
        _('geschatte kosten'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Geschatte kosten in euro\'s')
    )
    actual_cost = models.DecimalField(
        _('werkelijke kosten'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Werkelijke kosten in euro\'s')
    )

    # Procurement
    vendor = models.CharField(_('leverancier'), max_length=200, blank=True)
    quote_amount = models.DecimalField(
        _('offertebedrag'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    quote_status = models.CharField(
        _('offertestatus'),
        max_length=15,
        choices=QuoteStatus.choices,
        default=QuoteStatus.NONE
    )
    po_number = models.CharField(_('inkoopordernummer'), max_length=50, blank=True)

    closed_at = models.DateTimeField(_('afgesloten op'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(_('aangemaakt op'), auto_now_add=True)
    updated_at = models.DateTimeField(_('bijgewerkt op'), auto_now=True)

    # Soft delete
    is_deleted = models.BooleanField(_('verwijderd'), default=False)
    deleted_at = models.DateTimeField(_('verwijderd op'), null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_requests',
        verbose_name=_('verwijderd door')
    )

    class Meta:
        verbose_name = _('reparatieverzoek')
        verbose_name_plural = _('reparatieverzoeken')
        ordering = ['-created_at']
        permissions = [
            ('can_triage', _('Kan verzoeken triageren')),
            ('can_assign', _('Kan verzoeken toewijzen')),
        ]

    def __str__(self):
        return f"#{self.id} - {self.title}"

    def get_absolute_url(self):
        return reverse('requests:detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Set closed_at when status changes to closed
        if self.status == self.Status.CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_date and self.status not in [self.Status.COMPLETED, self.Status.CLOSED]:
            return self.due_date < timezone.now().date()
        return False

    @property
    def is_urgent(self):
        return self.priority == self.Priority.URGENT


class Attachment(models.Model):
    """File attachment for a repair request."""
    repair_request = models.ForeignKey(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('reparatieverzoek')
    )
    file = models.FileField(_('bestand'), upload_to=attachment_path)
    title = models.CharField(_('titel'), max_length=200, blank=True)
    uploaded_at = models.DateTimeField(_('geüpload op'), auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('geüpload door')
    )

    class Meta:
        verbose_name = _('bijlage')
        verbose_name_plural = _('bijlagen')
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title or os.path.basename(self.file.name)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def display_name(self):
        """Return title if set, otherwise filename."""
        return self.title or self.filename

    @property
    def is_image(self):
        ext = os.path.splitext(self.file.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    @property
    def file_icon(self):
        """Return Bootstrap icon class based on file type."""
        ext = os.path.splitext(self.file.name)[1].lower()
        icons = {
            '.pdf': 'bi-file-earmark-pdf',
            '.doc': 'bi-file-earmark-word',
            '.docx': 'bi-file-earmark-word',
            '.xls': 'bi-file-earmark-excel',
            '.xlsx': 'bi-file-earmark-excel',
            '.txt': 'bi-file-earmark-text',
            '.zip': 'bi-file-earmark-zip',
            '.rar': 'bi-file-earmark-zip',
        }
        return icons.get(ext, 'bi-file-earmark')

    @property
    def icon_color(self):
        """Return color class based on file type."""
        ext = os.path.splitext(self.file.name)[1].lower()
        colors = {
            '.pdf': 'text-danger',
            '.doc': 'text-primary',
            '.docx': 'text-primary',
            '.xls': 'text-success',
            '.xlsx': 'text-success',
        }
        return colors.get(ext, 'text-secondary')

    @property
    def thumbnail_url(self):
        """Return Cloudinary thumbnail URL for images."""
        if not self.is_image:
            return None
        url = self.file.url
        # Insert Cloudinary transformation for thumbnail
        if 'res.cloudinary.com' in url and '/upload/' in url:
            return url.replace('/upload/', '/upload/c_thumb,w_200,h_200/')
        return url

    @property
    def secure_url(self):
        """Return URL that goes through auth proxy."""
        return reverse('requests:serve_attachment', kwargs={
            'pk': self.repair_request_id,
            'attachment_pk': self.pk
        })

    @property
    def secure_thumbnail_url(self):
        """Return proxied thumbnail URL for images."""
        if not self.is_image:
            return None
        # For thumbnails, we still use Cloudinary directly as they're small previews
        # The full image requires authentication
        return self.thumbnail_url


class WorkLog(models.Model):
    """Activity log entry for a repair request."""

    class EntryType(models.TextChoices):
        CREATED = 'created', _('Nieuw')
        NOTE = 'note', _('Notitie')
        STATUS_CHANGE = 'status_change', _('Statuswijziging')
        ASSIGNMENT = 'assignment', _('Toewijzing')
        TIME_SPENT = 'time_spent', _('Tijdsbesteding')

    repair_request = models.ForeignKey(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='work_logs',
        verbose_name=_('reparatieverzoek')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('auteur')
    )
    entry_type = models.CharField(
        _('type'),
        max_length=20,
        choices=EntryType.choices,
        default=EntryType.NOTE
    )
    note = models.TextField(_('notitie'))
    minutes_spent = models.PositiveIntegerField(
        _('minuten besteed'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('aangemaakt op'), auto_now_add=True)

    class Meta:
        verbose_name = _('logboekregel')
        verbose_name_plural = _('logboekregels')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.created_at}"


class Notification(models.Model):
    """In-app notification for users."""

    class NotificationType(models.TextChoices):
        MENTION = 'mention', _('Vermelding')
        ASSIGNMENT = 'assignment', _('Toewijzing')
        STATUS_CHANGE = 'status_change', _('Statuswijziging')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('gebruiker')
    )
    notification_type = models.CharField(
        _('type'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.MENTION
    )
    title = models.CharField(_('titel'), max_length=200)
    message = models.TextField(_('bericht'))
    repair_request = models.ForeignKey(
        RepairRequest,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('reparatieverzoek'),
        null=True,
        blank=True
    )
    is_read = models.BooleanField(_('gelezen'), default=False)
    created_at = models.DateTimeField(_('aangemaakt op'), auto_now_add=True)

    class Meta:
        verbose_name = _('notificatie')
        verbose_name_plural = _('notificaties')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"
