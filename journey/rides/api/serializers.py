import math
from typing import Any
from django.db.models import Q
from rest_framework import serializers, status

from journey.rides.models import Rate
from journey.users.models import Driver, Rider
from journey.utils.exceptions import CustomValidationError

class RequestRideSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=13, decimal_places=10)
    longitude = serializers.DecimalField(max_digits=13, decimal_places=10)

    def validate(self, data):
        user = self.context['request'].user

        if not Rate.objects.filter(active=True).exists():
            raise CustomValidationError(
                {
                    "error": {
                        "type": "RATE_VALIDATION_ERROR",
                        "reason": "No active rate found"
                    }
                },
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        rider = Rider.objects.filter(user=user)
        if not rider.exists():
            raise CustomValidationError(
                {
                    "error": {
                        "type": "PROFILE_VALIDATION_ERROR",
                        "reason": "User is not a Rider"
                    }
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        if not rider.first().payment_source:
            raise CustomValidationError(
                {
                    "error": {
                        "type": "PAYMENT_METHOD_VALIDATION_ERROR",
                        "reason": "Rider does not have a payment sources"
                    }
                },
                status_code=status.HTTP_428_PRECONDITION_REQUIRED
            )
        
        self.drivers = Driver.objects.exclude(Q(rides_as_driver__active=True))
        if not self.drivers.exists():
            raise CustomValidationError(
                {
                    "error": {
                        "type": "AVAILABLE_DRIVERS_VALIDATION_ERROR",
                        "reason": "No available drivers found"
                    }
                },
                status_code=status.HTTP_404_NOT_FOUND
            )

        return data
    
    def to_representation(self, instance: Any) -> Any:
        data =  super().to_representation(instance)
        data['drivers'] = self.drivers
        return data


class RateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rate
        exclude = ['active']
