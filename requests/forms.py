from django import forms
from django.contrib.auth import get_user_model
from django.forms.widgets import FileInput
from django.utils.translation import gettext_lazy as _

from core.models import Asset, Location

User = get_user_model()

from .models import Attachment, RepairRequest, WorkLog


class MultipleFileInput(FileInput):
    """File input that allows multiple files."""
    allow_multiple_selected = True


class RepairRequestForm(forms.ModelForm):
    """Form for submitting a new repair request."""

    photos = forms.FileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control form-control-lg',
            'accept': 'image/*,.pdf',
        }),
        label=_("Foto's toevoegen"),
        help_text=_('Optioneel: voeg foto\'s toe van het probleem (max 10MB per bestand)')
    )

    class Meta:
        model = RepairRequest
        fields = [
            'title',
            'description',
            'location',
            'asset',
            'priority',
            'requester_name',
            'requester_email',
            'requester_phone',
            'preferred_contact_method',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('Kort omschrijven wat er aan de hand is'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 4,
                'placeholder': _('Geef meer details over het probleem'),
            }),
            'location': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'asset': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'requester_name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('Uw naam'),
            }),
            'requester_email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('uw@email.nl'),
            }),
            'requester_phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('06-12345678'),
            }),
            'preferred_contact_method': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Make asset optional with empty label
        self.fields['asset'].required = False
        self.fields['asset'].empty_label = _('(Niet van toepassing)')

        # Location is required
        self.fields['location'].empty_label = _('Kies een locatie')

        # Pre-fill for logged-in users
        if self.user and self.user.is_authenticated:
            if not self.initial.get('requester_name'):
                self.initial['requester_name'] = self.user.get_full_name() or self.user.username
            if not self.initial.get('requester_email'):
                self.initial['requester_email'] = self.user.email

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and self.user.is_authenticated:
            instance.requester_user = self.user
        if commit:
            instance.save()
        return instance


class AttachmentForm(forms.ModelForm):
    """Form for uploading attachments."""

    class Meta:
        model = Attachment
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-lg',
                'accept': 'image/*,.pdf',
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_('Bestand is te groot (max 10MB).'))

            # Check file type
            allowed_types = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf']
            ext = file.name.lower().split('.')[-1]
            if f'.{ext}' not in allowed_types:
                raise forms.ValidationError(
                    _('Alleen afbeeldingen en PDF-bestanden zijn toegestaan.')
                )
        return file


class WorkLogForm(forms.ModelForm):
    """Form for adding a work log entry."""

    class Meta:
        model = WorkLog
        fields = ['note', 'minutes_spent']
        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 3,
                'placeholder': _('Voeg een notitie toe...'),
            }),
            'minutes_spent': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': 0,
                'placeholder': _('Optioneel'),
            }),
        }


class TriageForm(forms.ModelForm):
    """Form for triaging/updating a repair request."""

    class Meta:
        model = RepairRequest
        fields = [
            'location', 'asset',
            'status', 'priority', 'assigned_to', 'due_date',
            'estimated_cost', 'actual_cost',
            'vendor', 'quote_amount', 'quote_status', 'po_number',
            'resolution_summary'
        ]
        widgets = {
            'location': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'asset': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
            }),
            'estimated_cost': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': '0',
                'step': '0.01',
                'placeholder': '€',
            }),
            'actual_cost': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': '0',
                'step': '0.01',
                'placeholder': '€',
            }),
            'vendor': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('Naam leverancier'),
            }),
            'quote_amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'min': '0',
                'step': '0.01',
                'placeholder': '€',
            }),
            'quote_status': forms.Select(attrs={
                'class': 'form-select form-select-lg',
            }),
            'po_number': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('PO-nummer'),
            }),
            'resolution_summary': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asset is optional
        self.fields['asset'].required = False
        self.fields['asset'].empty_label = _('(Geen)')
        # Exclude superusers (admin) from assignee list
        self.fields['assigned_to'].queryset = User.objects.filter(
            is_active=True,
            is_superuser=False
        ).order_by('first_name', 'last_name')
