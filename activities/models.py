from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import UniqueConstraint


class Address(models.Model):
    street = models.CharField(max_length=250, null=True)
    city = models.CharField(max_length=250, null=True)
    state = models.CharField(max_length=250, null=True)
    country = models.CharField(max_length=250, null=True)
    postal_code = models.CharField(max_length=250, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.country}"


class ExternalLinks(models.Model):
    wikipedia_url = models.URLField(null=True, max_length=500)
    website_url = models.URLField(null=True, max_length=500)


class Entity(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=250)
    description = models.TextField(null=True)
    images = ArrayField(models.URLField(), blank=True, default=list)
    destination_resource = models.CharField(max_length=250, default='user')
    migration_data = models.JSONField(default=dict)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, null=True)
    # point_field = PointField(null=True)
    external_links = models.ForeignKey(ExternalLinks, on_delete=models.CASCADE, null=True)
    tags = ArrayField(models.CharField(max_length=250), blank=True, default=list)
    original_language = models.CharField(max_length=250, null=False, default='pl')

    def __str__(self):
        return self.name


class Like(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class Comment(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class View(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['activity', 'user'],
                name='unique_view'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class Save(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"
