from rest_framework import serializers
from .models import User, Activity, ActivityLike, ActivitySave


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'

class ActivityLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLike
        fields = '__all__'

class ActivitySaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySave
        fields = '__all__'
