from django.contrib import admin
from .models import EmailAccount, EmailMessage

# Register your models here.
admin.site.register(EmailAccount)
admin.site.register(EmailMessage)
