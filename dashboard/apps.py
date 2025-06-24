# dashboard/apps.py

from django.apps import AppConfig
import threading


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        def start_if_tables_exist():
            from django.db import connection
            if not connection.introspection.table_names():
                return
            from .mail_checker import start_realtime_listeners
            start_realtime_listeners()

        threading.Thread(target=start_if_tables_exist, daemon=True).start()