from rest_framework import serializers
from .models import OpenTripMapServiceData, DataMigrationResource

class OpenTripMapServiceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenTripMapServiceData
        fields = '__all__'

class DataMigrationResourceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataMigrationResource
        fields = '__all__'
