from celery import shared_task
from .models import EmailAccount
from .mail_checker import monitor_email
import json
from django.core.cache import cache
from celery.utils.log import get_task_logger
from datetime import datetime
import time

logger = get_task_logger(__name__)

@shared_task(bind=True, name='monitor_emails')
def monitor_emails(self):
    """
    Celery task to monitor emails for all accounts
    """
    task_id = self.request.id
    logger.info(f"Starting email monitoring task {task_id}")
    
    try:
        # Get all email accounts
        accounts = EmailAccount.objects.all()
        results = []
        
        # Process each account
        for account in accounts:
            try:
                logger.info(f"Monitoring emails for account: {account.email_user_name}")
                # Monitor emails for this account and get results
                monitoring_result = monitor_email(
                    account.email_user_name,
                    account.password,
                    account.imap_host_name
                )
                
                # Store the results
                results.append({
                    'email': account.email_user_name,
                    'status': 'success',
                    'monitoring_result': monitoring_result
                })
                
                # Cache individual account results
                cache_key = f'email_monitoring_{account.email_user_name}'
                cache.set(cache_key, monitoring_result, timeout=3600)
                
            except Exception as e:
                logger.error(f"Error monitoring account {account.email_user_name}: {str(e)}")
                results.append({
                    'email': account.email_user_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Store the overall results in cache
        cache.set('email_monitoring_status', {
            'task_id': task_id,
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }, timeout=3600)
        
        logger.info(f"Completed email monitoring task {task_id}")
        return results
    except Exception as e:
        logger.error(f"Error in email monitoring task {task_id}: {str(e)}")
        cache.set('email_monitoring_status', {
            'task_id': task_id,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, timeout=3600)
        raise

@shared_task(bind=True, name='get_email_data', max_retries=3)
def get_email_data(self):
    """
    Celery task to get email data for all accounts
    """
    try:
        # Try to get data from cache first
        cached_data = cache.get('email_monitoring_status')
        if cached_data:
            logger.info("Retrieved data from cache")
            return cached_data

        # If no cached data, get fresh data
        accounts = EmailAccount.objects.all()
        results = []
        
        for account in accounts:
            try:
                logger.info(f"Monitoring emails for account: {account.email_user_name}")
                monitoring_result = monitor_email(
                    account.email_user_name,
                    account.password,
                    account.imap_host_name
                )
                
                results.append({
                    'email': account.email_user_name,
                    'status': 'success',
                    'monitoring_result': monitoring_result
                })
                
                # Cache individual account results
                cache_key = f'email_monitoring_{account.email_user_name}'
                cache.set(cache_key, monitoring_result, timeout=3600)
                
            except Exception as e:
                logger.error(f"Error monitoring account {account.email_user_name}: {str(e)}")
                results.append({
                    'email': account.email_user_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Store the overall results in cache
        data = {
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        cache.set('email_monitoring_status', data, timeout=3600)
        
        return data
        
    except Exception as e:
        logger.error(f"Error in get_email_data task: {str(e)}")
        # Retry the task with exponential backoff
        retry_in = (2 ** self.request.retries) * 5  # 5, 10, 20 seconds
        self.retry(exc=e, countdown=retry_in) 