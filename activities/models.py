from django.contrib.auth.models import BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.db import models
from transformers import pipeline
import logging

classifier = pipeline("text-classification", model="distilbert-base-uncased")


def classify_activity(name, description):
    logger = logging.getLogger(__name__)
    text = f"{name}. {description}"
    result = classifier(text)[0]
    result = classifier(text)[0]
    logger.error(f"Classification result: {result}")  # Debugowanie wyników klasyfikacji
    label_map = {
        "LABEL_0": "atrakcja",
        "LABEL_1": "restauracja",
        "LABEL_2": "podróż",
        "LABEL_3": "zakwaterowanie"
    }
    return label_map.get(result['label'], "unknown")


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


# TODO: improve user parameter to AbstractUser
class User(models.Model):
    email = models.CharField(max_length=250, unique=True, null=False, blank=False)
    account_verified = models.BooleanField(default=False)
    username = models.CharField(max_length=250, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_anonymous = False
    is_authenticated = False

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username


class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.user.username}' - {self.code}"


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
    activity_type = models.CharField(max_length=50, default='unknown')

    # def liked(self):
    #     return ActivityLike.objects.filter(activity=self).count()

    # def comments(self):
    #     return ActivityComment.objects.filter(activity=self).count()

    # def views(self):
    #     return ActivityView.objects.filter(activity=self).count()

    def save(self, *args, **kwargs):
        self.activity_type = classify_activity(self.name, self.description)
        super().save(*args, **kwargs)

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
