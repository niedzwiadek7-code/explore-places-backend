from django.contrib.postgres.fields import ArrayField
from django.db import models

from accounts.models import User


class Activity(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=250)
    description = models.TextField(null=True)
    images = ArrayField(models.URLField(), blank=True, default=list)
    destination_resource = models.CharField(max_length=250, default='user')
    migration_data = models.JSONField(default=dict)
    address = models.CharField(max_length=250, null=True)
    city = models.CharField(max_length=250, null=True)
    state = models.CharField(max_length=250, null=True)
    country = models.CharField(max_length=250, null=True)
    postal_code = models.CharField(max_length=250, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    wikipedia_url = models.URLField(null=True)
    website_url = models.URLField(null=True)

    tags = ArrayField(models.CharField(max_length=250), blank=True, default=list)

    def __str__(self):
        return self.name

class ActivityLike(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"

class ActivityComment(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"

class ActivityView(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"

class ActivitySave(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"
