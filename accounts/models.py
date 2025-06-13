from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)

    def __str__(self):
        return self.user.username


