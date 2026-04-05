from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    avatar_url = models.URLField(max_length=500, blank=True, default="")
    favorite_genres = models.JSONField(default=list, blank=True)
    country_code = models.CharField(max_length=5, default="US")

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username
