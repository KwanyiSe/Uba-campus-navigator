from rest_framework import serializers
from.models import Building

#create a serializer for converting buildings to json

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = "__all__"