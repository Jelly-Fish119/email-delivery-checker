from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        from django.db import connection
        if connection.introspection.table_names():
            import threading
            from .mail_checker import insert_all_emails_background
            from .models import EmailAccount
            accounts = EmailAccount.objects.all()
            if not threading.main_thread().is_alive():
                return
            for acc in accounts:
                print('-----'*10)
                threading.Thread(target=insert_all_emails_background, args=(acc,), daemon=True).start()