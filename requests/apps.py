from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RequestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'requests'
    verbose_name = _('Reparatieverzoeken')
