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
        from .mail_checker import listen_for_emails, check_folders

        def start_realtime_listeners():
            accounts = EmailAccount.objects.all()
            for account in accounts:
                folders = check_folders(account.imap_host_name)
                for folder in folders:
                    threading.Thread(
                        target=listen_for_emails,
                        args=(account.email_address, account.password, account.imap_host_name, folder),
                        daemon=True
                    ).start()

        threading.Thread(target=start_realtime_listeners, daemon=True).start()
