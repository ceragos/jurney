from django.contrib.auth import get_user_model
from rest_framework import serializers, status

from journey.rides.models import Rider, Driver
from journey.utils.exceptions import CustomValidationError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "name", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "username"},
        }

class RiderPaymentMethodSerializer(serializers.ModelSerializer):
    tokenized_card = serializers.CharField(max_length=50)
    acceptance_token = serializers.CharField()
    payment_source = serializers.CharField(read_only=True)

    class Meta:
        model = Rider
        fields = ["payment_source", "tokenized_card", "acceptance_token"]
        read_only_fields = ["payment_source"]
    
    def validate(self, data):
        user = self.context['request'].user
        if not Rider.objects.filter(user=user).exists():
            raise CustomValidationError(
                {
                    "error": {
                        "type": "PROFILE_VALIDATION_ERROR",
                        "reason": "User is not a Rider"
                    }
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        return data

class RideUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "email", "username"]

class DriverSerializer(serializers.ModelSerializer):
    user = RideUserSerializer()

    class Meta:
        model = Driver
        fields = ['user']


class RiderSerializer(serializers.ModelSerializer):
    user = RideUserSerializer()

    class Meta:
        model = Rider
        fields = ['user']
