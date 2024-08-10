from rest_framework import serializers
from .models import Activity, ActivityLike, ActivitySave


class ActivitySerializer(serializers.ModelSerializer):
    liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = '__all__'

    def get_liked_by_user(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ActivityLike.objects.filter(activity=obj, user=user).exists()


class ActivityLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLike
        fields = '__all__'

class ActivitySaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySave
        fields = '__all__'
