from django.db import models

# Create your models here.


class IPLog(models.Model):
    ip = models.TextField()

class ReleaseCode(models.Model):
    code = models.CharField(max_length = 6)
    trade_id = models.CharField(max_length = 50)
    
