from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    """Physical location in the facility."""
    name = models.CharField(_('naam'), max_length=200)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('bovenliggende locatie')
    )
    notes = models.TextField(_('notities'), blank=True)
    created_at = models.DateTimeField(_('aangemaakt op'), auto_now_add=True)
    updated_at = models.DateTimeField(_('bijgewerkt op'), auto_now=True)

    class Meta:
        verbose_name = _('locatie')
        verbose_name_plural = _('locaties')
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name

    def get_full_path(self):
        """Return full location path."""
        parts = [self.name]
        parent = self.parent
        while parent:
            parts.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(parts)


class Asset(models.Model):
    """Equipment or installation tracked for maintenance."""

    class Status(models.TextChoices):
        OPERATIONAL = 'operational', _('Operationeel')
        ATTENTION = 'attention', _('Aandacht Nodig')
        OUT_OF_SERVICE = 'out_of_service', _('Buiten Gebruik')
        DISPOSED = 'disposed', _('Afgevoerd')

    class Criticality(models.TextChoices):
        LOW = 'low', _('Laag')
        MEDIUM = 'medium', _('Middel')
        HIGH = 'high', _('Hoog')

    class Category(models.TextChoices):
        HVAC = 'hvac', _('HVAC / Klimaat')
        ELECTRICAL = 'electrical', _('Elektrisch')
        PLUMBING = 'plumbing', _('Sanitair')
        SAFETY = 'safety', _('Veiligheid')
        AV = 'av', _('Audio/Video')
        FURNITURE = 'furniture', _('Meubilair')
        BUILDING = 'building', _('Gebouw')
        OTHER = 'other', _('Overig')

    asset_tag = models.CharField(
        _('objectnummer'),
        max_length=50,
        unique=True,
        help_text=_('Uniek identificatienummer, bijv. HVAC-01')
    )
    name = models.CharField(_('naam'), max_length=200)
    category = models.CharField(
        _('categorie'),
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name=_('locatie')
    )
    manufacturer = models.CharField(_('fabrikant'), max_length=200, blank=True)
    model = models.CharField(_('model'), max_length=200, blank=True)
    serial_number = models.CharField(_('serienummer'), max_length=200, blank=True)
    install_date = models.DateField(_('installatiedatum'), null=True, blank=True)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.OPERATIONAL
    )
    criticality = models.CharField(
        _('kritiekheid'),
        max_length=10,
        choices=Criticality.choices,
        default=Criticality.MEDIUM
    )
    warranty_end_date = models.DateField(_('garantie tot'), null=True, blank=True)
    photo = models.ImageField(
        _('foto'),
        upload_to='assets/',
        null=True,
        blank=True
    )
    description = models.TextField(_('omschrijving'), blank=True)
    is_monument = models.BooleanField(
        _('rijksmonument'),
        default=False,
        help_text=_('Dit object valt onder monumentenzorg')
    )
    # Replacement tracking
    replacement_date = models.DateField(
        _('geplande vervanging'),
        null=True,
        blank=True,
        help_text=_('Datum waarop dit object vervangen moet worden')
    )
    replacement_notes = models.TextField(
        _('vervangingsnotities'),
        blank=True,
        help_text=_('Reden voor vervanging, specificaties voor nieuw object, etc.')
    )
    # Periodic maintenance (legacy - use MaintenanceSchedule instead)
    maintenance_interval_days = models.PositiveIntegerField(
        _('onderhoudsinterval (dagen)'),
        null=True,
        blank=True,
        help_text=_('Aantal dagen tussen onderhoudsbeurten')
    )
    last_maintenance_date = models.DateField(
        _('laatste onderhoud'),
        null=True,
        blank=True
    )
    maintenance_notes = models.TextField(
        _('onderhoudsinstructies'),
        blank=True,
        help_text=_('Wat moet er gedaan worden bij onderhoud?')
    )
    created_at = models.DateTimeField(_('aangemaakt op'), auto_now_add=True)
    updated_at = models.DateTimeField(_('bijgewerkt op'), auto_now=True)

    class Meta:
        verbose_name = _('object')
        verbose_name_plural = _('objecten')
        ordering = ['asset_tag']

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    def get_absolute_url(self):
        return reverse('assets:detail', kwargs={'pk': self.pk})

    @property
    def next_maintenance_date(self):
        """Calculate when next maintenance is due."""
        if not self.maintenance_interval_days:
            return None
        if not self.last_maintenance_date:
            # If never maintained, it's due now
            from datetime import date
            return date.today()
        from datetime import timedelta
        return self.last_maintenance_date + timedelta(days=self.maintenance_interval_days)

    @property
    def maintenance_due(self):
        """Check if maintenance is due or overdue."""
        next_date = self.next_maintenance_date
        if not next_date:
            return False
        from datetime import date
        return next_date <= date.today()

    @property
    def days_until_maintenance(self):
        """Days until next maintenance (negative if overdue)."""
        next_date = self.next_maintenance_date
        if not next_date:
            return None
        from datetime import date
        return (next_date - date.today()).days

    @property
    def replacement_due(self):
        """Check if replacement is due or overdue."""
        if not self.replacement_date:
            return False
        from datetime import date
        return self.replacement_date <= date.today()

    @property
    def days_until_replacement(self):
        """Days until replacement (negative if overdue)."""
        if not self.replacement_date:
            return None
        from datetime import date
        return (self.replacement_date - date.today()).days

    def save(self, *args, **kwargs):
        if not self.asset_tag:
            import uuid
            # Auto-generate asset tag based on category + UUID fragment
            prefix_map = {
                'hvac': 'HVAC',
                'electrical': 'ELEK',
                'plumbing': 'SAN',
                'safety': 'VEIL',
                'av': 'AV',
                'furniture': 'MEUB',
                'building': 'GEB',
                'other': 'OBJ',
            }
            prefix = prefix_map.get(self.category, 'OBJ')
            # Use first 6 chars of UUID (uppercase)
            uid = uuid.uuid4().hex[:6].upper()
            self.asset_tag = f"{prefix}-{uid}"
        super().save(*args, **kwargs)


class MaintenanceSchedule(models.Model):
    """Periodic maintenance schedule for an asset."""
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='maintenance_schedules',
        verbose_name=_('object')
    )
    name = models.CharField(
        _('onderhoudstaak'),
        max_length=200,
        help_text=_('Bijv. "Filter vervangen", "Jaarlijkse inspectie"')
    )
    interval_days = models.PositiveIntegerField(
        _('interval (dagen)'),
        help_text=_('Aantal dagen tussen onderhoudsbeurten')
    )
    last_performed = models.DateField(
        _('laatst uitgevoerd'),
        null=True,
        blank=True
    )
    notes = models.TextField(
        _('instructies'),
        blank=True,
        help_text=_('Wat moet er gedaan worden?')
    )
    created_at = models.DateTimeField(_('aangemaakt op'), auto_now_add=True)

    class Meta:
        verbose_name = _('onderhoudsschema')
        verbose_name_plural = _("onderhoudsschema's")
        ordering = ['asset', 'name']

    def __str__(self):
        return f"{self.asset.asset_tag} - {self.name}"

    @property
    def next_due_date(self):
        """Calculate when this maintenance is next due."""
        if not self.last_performed:
            from datetime import date
            return date.today()
        from datetime import timedelta
        return self.last_performed + timedelta(days=self.interval_days)

    @property
    def is_due(self):
        """Check if maintenance is due or overdue."""
        from datetime import date
        return self.next_due_date <= date.today()

    @property
    def days_until_due(self):
        """Days until due (negative if overdue)."""
        from datetime import date
        return (self.next_due_date - date.today()).days
