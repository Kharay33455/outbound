from django.db import models

# Create your models here.


class IPLog(models.Model):
    ip = models.TextField()
    
