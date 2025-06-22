# import os
# from celery import Celery
# from celery.signals import worker_ready
# from django.conf import settings

# # Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'email_checker_pro.settings')

# app = Celery('email_checker_pro')

# # Using a string here means the worker doesn't have to serialize
# # the configuration object to child processes.
# app.config_from_object('django.conf:settings', namespace='CELERY')

# # Load task modules from all registered Django app configs.
# app.autodiscover_tasks()

# # Configure Celery to be more resilient and handle serialization issues
# app.conf.update(
#     broker_connection_retry=True,
#     broker_connection_retry_on_startup=True,
#     broker_connection_max_retries=10,
#     broker_pool_limit=10,
#     result_expires=3600,  # Results expire after 1 hour
#     task_acks_late=True,
#     task_reject_on_worker_lost=True,
#     task_track_started=True,
#     worker_prefetch_multiplier=1,
#     broker_connection_timeout=30,
#     # Add these new configurations to handle serialization issues
#     task_serializer='json',
#     accept_content=['json'],
#     result_serializer='json',
#     timezone='UTC',
#     enable_utc=True,
#     # Add task routing to ensure proper task handling
#     task_routes={
#         'dashboard.tasks.*': {'queue': 'default'},
#     },
#     # Add task default settings
#     task_default_queue='default',
#     task_default_exchange='default',
#     task_default_routing_key='default',
#     # Add result backend settings
#     result_backend_transport_options={
#         'retry_policy': {
#             'timeout': 5.0
#         }
#     }
# )

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')