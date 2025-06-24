from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix auto-increment sequence for EmailAccount'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT setval(pg_get_serial_sequence('dashboard_emailaccount', 'id'), (SELECT MAX(id) FROM dashboard_emailaccount));")
        self.stdout.write(self.style.SUCCESS('Sequence fixed for dashboard_emailaccount.'))
