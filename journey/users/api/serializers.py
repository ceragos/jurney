from django.contrib.auth import get_user_model
from rest_framework import serializers

from journey.rides.models import Rider

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "username"},
        }

class RiderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rider
        fields = ["tokenized_card"]

    def validate(self, data):
        user = self.context['request'].user
        try:
            Rider.objects.get(user=user)
        except Rider.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "error": {
                        "type": "PROFILE_VALIDATION_ERROR",
                        "reason": "User is not a Rider"
                    }
                }
            )

        return data
