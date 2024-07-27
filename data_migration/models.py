from django.db import models


class DataMigrationResource(models.Model):
    name = models.CharField(max_length=250)
    base_url = models.URLField()
    credentials = models.JSONField(default=dict)

class OpenTripMapServiceData(models.Model):
    min_longitude = models.FloatField()
    min_latitude = models.FloatField()
    max_longitude = models.FloatField()
    max_latitude = models.FloatField()
    imported_at = models.DateTimeField(auto_now_add=True)
