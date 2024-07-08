from django.db import models

class User(models.Model):
    email = models.CharField(max_length=250, unique=True, null=False, blank=False)
    username = models.CharField(max_length=250)

    def __str__(self):
        return self.username

class Activity(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    description = models.TextField()
    start_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
