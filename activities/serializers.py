from math import radians, sin, cos, sqrt, atan2
from rest_framework import serializers

from utils.geo_utils import Location
from .models import Entity as ActivityEntity, Like as ActivityLike, Save as ActivitySave, Address, ExternalLinks, \
    Comment as ActivityComment


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class ExternalLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalLinks
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = ActivityComment
        fields = '__all__'

    def get_user(self, obj):
        return obj.user.username


class ActivitySerializer(serializers.ModelSerializer):
    liked_by_user = serializers.SerializerMethodField()
    # coordinates = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    address = AddressSerializer(read_only=True)
    external_links = ExternalLinksSerializer()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = ActivityEntity
        fields = '__all__'

    def get_liked_by_user(self, obj):
        if (
                not self.context.get('request') or
                not hasattr(self.context['request'], 'user')
        ):
            return False

        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ActivityLike.objects.filter(activity=obj, user=user).exists()

    def get_distance(self, obj):
        if obj.distance:
            return obj.distance

        return None

    def get_comments(self, obj):
        # Filter comments related to the current activity
        comments = ActivityComment.objects.filter(activity=obj)
        return CommentSerializer(comments, many=True).data


class ActivityLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLike
        fields = '__all__'


class ActivitySaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySave
        fields = '__all__'
