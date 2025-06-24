# dashboard/apps.py

from django.apps import AppConfig
import threading


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        from django.db import connection
        if not connection.introspection.table_names():
            return

        from .models import EmailAccount
        from .mail_checker import start_realtime_listeners

        threading.Thread(target=start_realtime_listeners, daemon=True).start()