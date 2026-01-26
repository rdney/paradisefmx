"""URL configuration for paradisefmx project."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin

from . import admin as custom_admin  # noqa: F401 - restricts admin to superusers
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('requests/', include('requests.urls')),
    path('assets/', include('core.urls_assets')),
    path('account/', include('accounts.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
