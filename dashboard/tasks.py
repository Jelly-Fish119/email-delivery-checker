# from celery import shared_task
# from django.core.cache import cache
# from celery.utils.log import get_task_logger
# from datetime import datetime
# import time
# from .models import EmailAccount
# from .mail_checker import get_emails_checker, insert_to_db, check_folders

# logger = get_task_logger(__name__)

# @shared_task(bind=True, max_retries=3, default_retry_delay=60)
# def fetch_and_insert_all_emails_task(self):
#     logger.info('running the fetch_and_insert_all_emails_task')
#     try:
#         accounts = EmailAccount.objects.all()
#         for account in accounts:
#             logger.info(f'Checking account: {account.email_address}')
#             try:
#                 folders = check_folders(account.imap_host_name)
#                 logger.info(f'Folders: {folders}')
#                 emails = get_emails_checker(
#                     account.email_address,
#                     account.password,
#                     account.imap_host_name,
#                     folders,
#                     since_days=None,
#                     since_mins=1,
#                     since_hours=None
#                 )
                
#                 if emails is None or len(emails) == 0:
#                     logger.warning(f'No emails returned for account: {account.email_address}')
#                     continue
                    
#                 logger.info(f"Total emails fetched: {len(emails)}")
#                 for i, email_data in enumerate(emails):
#                     logger.info(f"Email {i}: {email_data}")
#                     try:
#                         if not email_data or not isinstance(email_data, dict):
#                             logger.info(f"Skipping invalid email_data: {email_data}")
#                             continue
#                         insert_to_db(email_data, account.email_address)
#                     except Exception as e:
#                         logger.error(f'Error during insert_to_db: {e}')
#                         continue
#                 logger.info(f'done for account {account.email_address}')
#             except Exception as e:
#                 logger.error(f'Error processing account {account.email_address}: {e}')
#                 continue
#         return 'done'
#     except Exception as e:
#         import traceback
#         logger.error('Unhandled error:', e)
#         logger.error(traceback.format_exc())
#         # Retry the task if it fails
#         raise self.retry(exc=e, countdown=60)
