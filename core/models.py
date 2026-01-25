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

    def save(self, *args, **kwargs):
        if not self.asset_tag:
            # Auto-generate asset tag based on category
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
            # Get next number for this category
            last = Asset.objects.filter(
                asset_tag__startswith=prefix
            ).order_by('-asset_tag').first()
            if last:
                try:
                    num = int(last.asset_tag.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.asset_tag = f"{prefix}-{num:03d}"
        super().save(*args, **kwargs)
