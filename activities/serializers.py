from math import radians, sin, cos, sqrt, atan2
from rest_framework import serializers
from .models import Entity as ActivityEntity, Like as ActivityLike, Save as ActivitySave, Address, ExternalLinks, \
    Translation, Comment as ActivityComment


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class ExternalLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalLinks
        fields = '__all__'


class ActivityTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
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
    coordinates = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    address = AddressSerializer(read_only=True)
    external_links = ExternalLinksSerializer()
    translation = serializers.SerializerMethodField()
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

    def get_coordinates(self, obj):
        if obj.point_field:
            return dict(
                latitude=obj.point_field.coords[1],
                longitude=obj.point_field.coords[0]
            )
        return None

    def get_translation(self, obj):
        request = self.context.get('request')

        if request and 'language' in request.data:
            if 'language' in request.data == obj.original_language:
                return None

            language = request.data.get('language')
            translation = Translation.objects.filter(
                language=language,
                activity=obj
            ).first()
            if translation:
                return ActivityTranslationSerializer(translation).data

        return None

    def get_distance(self, obj):
        if not self.context.get('user_location'):
            return None

        user_location = self.context['user_location']
        obj_location = obj.point_field
        if not obj_location:
            return None

        lat1, lon1 = user_location.y, user_location.x
        lat2, lon2 = obj_location.y, obj_location.x
        R = 6371000

        φ1 = radians(lat1)
        φ2 = radians(lat2)
        Δφ = radians(lat2 - lat1)
        Δλ = radians(lon2 - lon1)

        a = sin(Δφ / 2) * sin(Δφ / 2) + cos(φ1) * cos(φ2) * sin(Δλ / 2) * sin(Δλ / 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance_in_meters = R * c
        return distance_in_meters

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
