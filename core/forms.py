from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Asset, Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'parent', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'parent': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'notes': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 3}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            'name', 'category', 'location',
            'manufacturer', 'model', 'serial_number',
            'install_date', 'status', 'criticality',
            'warranty_end_date', 'photo', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'category': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'location': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'model': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'install_date': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'criticality': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'warranty_end_date': forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control form-control-lg', 'accept': 'image/*'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 3}),
        }
