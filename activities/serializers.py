from rest_framework import serializers
from .models import Entity as ActivityEntity, Like as ActivityLike, Save as ActivitySave, Address, ExternalLinks


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class ExternalLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalLinks
        fields = '__all__'


class ActivitySerializer(serializers.ModelSerializer):
    liked_by_user = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    address = AddressSerializer(read_only=True)
    external_links = ExternalLinksSerializer()

    class Meta:
        model = ActivityEntity
        fields = '__all__'

    def get_liked_by_user(self, obj):
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


class ActivityLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLike
        fields = '__all__'


class ActivitySaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivitySave
        fields = '__all__'
