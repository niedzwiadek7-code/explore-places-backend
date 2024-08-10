from rest_framework import serializers
from accounts.models import Entity as UserEntity


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEntity
        fields = '__all__'
