from django.apps import AppConfig
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):
        from django.db import connection
        if connection.introspection.table_names():
            if not threading.main_thread().is_alive():
                return
            # Start the background email fetching thread
            threading.Thread(target=self.run_email_fetching_scheduler, daemon=True).start()

    def run_email_fetching_scheduler(self):
        """Run email fetching every second"""
        while True:
            try:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting email fetch cycle...")
                fetch_and_insert_all_emails_background()
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Email fetch cycle completed")
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error in email fetch cycle: {e}")
            
            # Wait for 1 second before next cycle
            time.sleep(30)


def get_all_accounts_emails(accounts, since_days=3650, since_hours=None, since_mins=None):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        from .mail_checker import get_emails_checker
        from .mail_checker import check_folders
        future_to_account = {
            executor.submit(get_emails_checker, acc.email_address, acc.password, acc.imap_host_name, check_folders(acc.imap_host_name), since_days, since_hours, since_mins): acc
            for acc in accounts
        }
        for future in as_completed(future_to_account):
            acc = future_to_account[future]
            try:
                emails = future.result()
                if emails:
                    for email in emails:
                        email['app_mail'] = acc.email_address
                    results.extend(emails)
            except Exception as exc:
                print(f'Account {acc.email_address} generated an exception: {exc}')
    return results


def fetch_and_insert_all_emails_background():
    from .models import EmailAccount
    from .mail_checker import insert_to_db
    accounts = EmailAccount.objects.all()
    all_emails = get_all_accounts_emails(accounts, since_days=None, since_hours=None, since_mins=1)
    for email_data in all_emails:
        try:
            insert_to_db(email_data, email_data['app_mail'])
        except Exception as e:
            print('error', e)
            continue