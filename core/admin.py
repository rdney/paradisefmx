from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Asset, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    list_filter = ['parent']
    search_fields = ['name', 'notes']
    ordering = ['name']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_tag', 'name', 'category', 'location', 'status', 'criticality']
    list_filter = ['status', 'criticality', 'category', 'location']
    search_fields = ['asset_tag', 'name', 'manufacturer', 'model', 'serial_number']
    ordering = ['asset_tag']
    fieldsets = [
        (None, {
            'fields': ['asset_tag', 'name', 'category', 'location']
        }),
        (_('Details'), {
            'fields': ['manufacturer', 'model', 'serial_number', 'install_date', 'warranty_end_date']
        }),
        (_('Status'), {
            'fields': ['status', 'criticality']
        }),
        (_('Media'), {
            'fields': ['photo', 'description']
        }),
    ]
