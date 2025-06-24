# dashboard/apps.py

from django.apps import AppConfig
import threading
from django.db.models.signals import post_migrate


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        from django.db import connection
        if not connection.introspection.table_names():
            return

        # Use post_migrate signal to ensure database is ready
        post_migrate.connect(self._start_listeners, sender=self)

    def _start_listeners(self, sender, **kwargs):
        from .mail_checker import start_realtime_listeners
        threading.Thread(target=start_realtime_listeners, daemon=True).start()