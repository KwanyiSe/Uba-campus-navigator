from rest_framework import serializers
from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = [
            "id",
            "name",
            "email",
            "subject",
            "message",
        ]

    def validate(self, attrs):
        request = self.context.get("request")

        if request and not request.user.is_authenticated:

            if not attrs.get("name"):
                raise serializers.ValidationError({
                    "name": "Name is required for guest users."
                })

            if not attrs.get("email"):
                raise serializers.ValidationError({
                    "email": "Email is required for guest users."
                })

        return attrs