from django.contrib.postgres.fields import ArrayField
from django.db import models

from accounts.models import Entity as UserEntity


class Address(models.Model):
    street = models.CharField(max_length=250, null=True)
    city = models.CharField(max_length=250, null=True)
    state = models.CharField(max_length=250, null=True)
    country = models.CharField(max_length=250, null=True)
    postal_code = models.CharField(max_length=250, null=True)

    def __str__(self):
        return f"{self.street}, {self.city}, {self.country}"


class Coordinates(models.Model):
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    def __str__(self):
        return f"{self.latitude}, {self.longitude}"


class ExternalLinks(models.Model):
    wikipedia_url = models.URLField(null=True)
    website_url = models.URLField(null=True)


class Entity(models.Model):
    owner = models.ForeignKey(UserEntity, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=250)
    description = models.TextField(null=True)
    images = ArrayField(models.URLField(), blank=True, default=list)
    destination_resource = models.CharField(max_length=250, default='user')
    migration_data = models.JSONField(default=dict)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, null=True)
    coordinates = models.ForeignKey(Coordinates, on_delete=models.CASCADE, null=True)
    external_links = models.ForeignKey(ExternalLinks, on_delete=models.CASCADE, null=True)
    tags = ArrayField(models.CharField(max_length=250), blank=True, default=list)

    def __str__(self):
        return self.name


class Like(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(UserEntity, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class Comment(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(UserEntity, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class View(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(UserEntity, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"


class Save(models.Model):
    activity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    user = models.ForeignKey(UserEntity, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity.name}"
