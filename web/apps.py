import sys

from django.apps import AppConfig

class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        if any(cmd in sys.argv for cmd in ['runserver', 'gunicorn', 'daphne']):
            import web.signals #noqa