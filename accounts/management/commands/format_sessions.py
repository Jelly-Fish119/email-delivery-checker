from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.db import transaction

class Command(BaseCommand):
    help = 'Formats and cleans up the session table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Only remove expired sessions',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup without confirmation',
        )

    def handle(self, *args, **options):
        expired_only = options['expired_only']
        force = options['force']

        # Get all sessions
        if expired_only:
            sessions = Session.objects.filter(expire_date__lt=timezone.now())
            self.stdout.write(f"Found {sessions.count()} expired sessions")
        else:
            sessions = Session.objects.all()
            self.stdout.write(f"Found {sessions.count()} total sessions")

        if not force:
            confirm = input(f"Are you sure you want to {'remove expired sessions' if expired_only else 'format all sessions'}? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Operation cancelled'))
                return

        try:
            with transaction.atomic():
                if expired_only:
                    sessions.delete()
                    self.stdout.write(self.style.SUCCESS(f'Successfully removed {sessions.count()} expired sessions'))
                else:
                    # Format all sessions
                    for session in sessions:
                        # Update session data if needed
                        session_data = session.get_decoded()
                        # You can modify session_data here if needed
                        session.session_data = session_data
                        session.save()
                    self.stdout.write(self.style.SUCCESS('Successfully formatted all sessions'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {str(e)}')) 