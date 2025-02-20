from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# Create your models here.
class CustomUser(AbstractUser):
    pass

class ChatMessage(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
    
@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class Stat(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class Server(models.Model):
    name = models.CharField(max_length=100)
    status = models.ForeignKey(Stat, on_delete=models.CASCADE)
    load_percentage = models.IntegerField()

    def __str__(self):
        return self.name