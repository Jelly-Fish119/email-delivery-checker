from django.core.management.base import BaseCommand
from dashboard.mail_checker import start_realtime_listeners

class Command(BaseCommand):
    help = 'Start IMAP real-time listeners'

    def handle(self, *args, **options):
        start_realtime_listeners()

