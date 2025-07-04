"""
WSGI config for email_checker_pro project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'email_checker_pro.settings')

application = get_wsgi_application()

# only import after application is ready
from dashboard.mail_checker import start_realtime_listeners
start_realtime_listeners()
