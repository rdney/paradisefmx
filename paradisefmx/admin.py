from django.contrib import admin


def superuser_has_permission(self, request):
    """Only allow superusers to access admin."""
    return request.user.is_active and request.user.is_superuser


# Restrict admin to superusers only
admin.site.has_permission = lambda request: superuser_has_permission(admin.site, request)
