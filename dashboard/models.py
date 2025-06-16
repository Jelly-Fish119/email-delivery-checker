from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class EmailAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email_address = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    imap_host_name = models.CharField(max_length=100)

    def __str__(self):
        return self.email_address

class EmailMonitoringResult(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    email_account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email_account.email_user_name} - {self.status}"

    def mark_completed(self, result=None):
        self.status = 'completed'
        self.result = result
        self.completed_at = timezone.now()
        self.save()

    def mark_failed(self, error=None):
        self.status = 'failed'
        self.error = error
        self.completed_at = timezone.now()
        self.save()

class EmailMessage(models.Model):
    email_account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    body = models.TextField()
    sender = models.CharField(max_length=100)
    date = models.DateTimeField()
    folder = models.CharField(max_length=10)
    
    def __str__(self):
        return self.subject 