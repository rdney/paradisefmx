from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Asset, Location, MaintenanceSchedule


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'created_at']
    list_filter = ['parent']
    search_fields = ['name', 'notes']
    ordering = ['name']


class MaintenanceScheduleInline(admin.TabularInline):
    model = MaintenanceSchedule
    extra = 1
    fields = ['name', 'interval_days', 'last_performed', 'notes']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_tag', 'name', 'category', 'location', 'status', 'criticality', 'replacement_date']
    list_filter = ['status', 'criticality', 'category', 'location']
    search_fields = ['asset_tag', 'name', 'manufacturer', 'model', 'serial_number']
    ordering = ['asset_tag']
    inlines = [MaintenanceScheduleInline]
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
        (_('Vervanging'), {
            'fields': ['replacement_date', 'replacement_notes']
        }),
        (_('Media'), {
            'fields': ['photo', 'description']
        }),
    ]


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ['asset', 'name', 'interval_days', 'last_performed', 'next_due_date', 'is_due']
    list_filter = ['asset__category', 'asset__location']
    search_fields = ['name', 'asset__name', 'asset__asset_tag']
    ordering = ['asset', 'name']
