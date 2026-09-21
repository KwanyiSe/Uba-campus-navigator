from rest_framework import serializers
from .models import Building


class BuildingSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = [f.name for f in Building._meta.fields] + ["photo_url"]

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        url = obj.photo.url
        return request.build_absolute_uri(url) if request else url
