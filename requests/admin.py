from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Attachment, RepairRequest, WorkLog


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']


class WorkLogInline(admin.TabularInline):
    model = WorkLog
    extra = 0
    readonly_fields = ['created_at', 'author', 'entry_type']
    ordering = ['-created_at']


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'status', 'priority', 'location',
        'requester_name', 'assigned_to', 'created_at'
    ]
    list_filter = ['status', 'priority', 'location', 'assigned_to']
    search_fields = ['title', 'description', 'requester_name', 'requester_email']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [AttachmentInline, WorkLogInline]

    fieldsets = [
        (None, {
            'fields': ['title', 'description', 'location', 'asset']
        }),
        (_('Melder'), {
            'fields': [
                'requester_name', 'requester_email', 'requester_phone',
                'preferred_contact_method', 'requester_user'
            ]
        }),
        (_('Status'), {
            'fields': ['status', 'priority', 'assigned_to', 'triaged_by', 'due_date']
        }),
        (_('Afronding'), {
            'fields': ['resolution_summary', 'closed_at'],
            'classes': ['collapse']
        }),
    ]
    readonly_fields = ['closed_at']


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ['repair_request', 'entry_type', 'author', 'created_at']
    list_filter = ['entry_type', 'author']
    search_fields = ['note', 'repair_request__title']
    ordering = ['-created_at']
