import math
from typing import Any
from django.db.models import Q
from rest_framework import serializers

from journey.rides.models import Rate
from journey.users.models import Driver, Rider
from journey.utils.distances import calculate_distance

class RequestRideSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)

    def validate(self, data):
        user = self.context['request'].user

        if not Rate.objects.filter(active=True).exists():
            raise serializers.ValidationError(
                {
                    "error": {
                        "type": "RATE_VALIDATION_ERROR",
                        "reason": "No active rate found"
                    }
                }
            )
        
        try:
            rider = Rider.objects.get(user=user)
        except Rider.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "error": {
                        "type": "PROFILE_VALIDATION_ERROR",
                        "reason": "User is not a Rider"
                    }
                }
            )

        if not rider.payment_source:
            raise serializers.ValidationError(
                {
                    "error": {
                        "type": "PAYMENT_METHOD_VALIDATION_ERROR",
                        "reason": "Rider does not have a payment sources"
                    }
                }
            )
        
        self.drivers = Driver.objects.exclude(Q(rides_as_driver__active=True))
        if not self.drivers.exists():
            raise serializers.ValidationError(
                {
                    "error": {
                        "type": "AVAILABLE_DRIVERS_VALIDATION_ERROR",
                        "reason": "No available drivers found"
                    }
                }
            )

        return data
    
    def to_representation(self, instance: Any) -> Any:
        data =  super().to_representation(instance)
        data['drivers'] = self.drivers
        return data
