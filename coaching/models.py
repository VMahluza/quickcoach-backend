from django.db import models
from authentication.models import User
import django_filters
from graphene_django.filter import DjangoFilterConnectionField

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class CoachingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_sessions')
    prompt = models.TextField()
    response = models.TextField()
    tags = models.ManyToManyField(Tag, related_name='coaching_sessions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session by {self.user.username} at {self.created_at}"