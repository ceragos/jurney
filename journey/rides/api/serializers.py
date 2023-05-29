from django.utils import timezone
import math
from typing import Any
from django.db.models import Q
from rest_framework import serializers, status

from journey.rides.models import Rate, Ride, Payments
from journey.users.models import Driver, Rider
from journey.users.api.serializers import DriverSerializer
from journey.utils.exceptions import CustomValidationError
from journey.utils.payment_platform import generate_transaction, get_transactions
from journey.utils.referrals import generate_payment_reference

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
        
        rider_q = Rider.objects.filter(user=user)
        if not rider_q.exists():
            raise CustomValidationError(
                {
                    "error": {
                        "type": "PROFILE_VALIDATION_ERROR",
                        "reason": "User is not a Rider"
                    }
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        rider = rider_q.first()
        if rider and not rider.payment_source:
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


class DataPaymentSerializer(serializers.ModelSerializer):
    ride = RateSerializer()

    class Meta:
        model = Payments
        fields = '__all__'
        read_only_fields = ['ride']


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payments
        fields = '__all__'

    def create(self, validated_data):
        ride = validated_data.pop('ride')
        reference = validated_data.pop('reference')
        duration = validated_data.pop('minutes_elapsed')
        distance = validated_data.pop('kilometers')
        total_amount = int(validated_data.pop('total_amount'))
        customer_email = ride.rider.user.email
        payment_source = ride.rider.payment_source

        try:
            transaction = generate_transaction(total_amount, customer_email, reference, payment_source)
            transaction_id = transaction['data']['id']
        except:
            raise CustomValidationError(
                'An error occurred during the transaction',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            payment = Payments.objects.create(
                ride=ride,
                reference=reference,
                minutes_elapsed=duration,
                kilometers=distance,
                total_amount=total_amount,
                transaction_id=transaction_id,
                transaction_response=transaction,
                status=transaction['data']['status']
            )

            transaction = get_transactions(transaction_id)
            payment.transaction_confirmation = transaction
            payment.status = transaction['data']['status']
            payment.save()
        except:
            raise CustomValidationError(
                'An error occurred while confirming the transaction',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return payment


class StartRideSerializer(serializers.ModelSerializer):
    driver = DriverSerializer()
    rate = RateSerializer()

    class Meta:
        model = Ride
        fields = ['id', 'driver', 'rate', 'start', 'starting_latitude', 'starting_longitude']


class FinisRideSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(max_digits=13, decimal_places=10)
    longitude = serializers.DecimalField(max_digits=13, decimal_places=10)
    payment = PaymentSerializer()

    class Meta:
        model = Ride
        fields = ['latitude', 'longitude', 'payment']
        read_only_fields = ['payment']

    def validate(self, data):
        user = self.context['request'].user
        ride = self.instance
        
        driver_q = Driver.objects.filter(user=user)
        if not driver_q.exists():
            raise CustomValidationError(
                {
                    "error": {
                        "type": "PROFILE_VALIDATION_ERROR",
                        "reason": "User is not a Driver"
                    }
                },
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        request_driver = driver_q.first()
        owner_driver = ride.driver
        if request_driver and owner_driver and owner_driver != request_driver:
            raise CustomValidationError(
                {
                    "error": {
                        "type": "DRIVER_VALIDATION_ERROR",
                        "reason": "Driver is not assigned to this Ride"
                    }
                },
                status_code=status.HTTP_403_FORBIDDEN
            )

        return data

    def update(self, instance, validated_data):
        latitude = validated_data.get('latitude', instance.final_latitude)
        longitude = validated_data.get('longitude', instance.final_longitude)

        instance.final_latitude = latitude
        instance.final_longitude = longitude
        instance.ends = timezone.now()
        instance.active = False
        instance.save()

        user = self.context['request'].user
        driver = Driver.objects.filter(user=user).first()

        if driver:
            driver.current_latitude = latitude
            driver.current_longitude = longitude
            driver.save()

        payment_data = {
            'ride': instance.id,
            'reference': generate_payment_reference(),
            'minutes_elapsed': instance.duration,
            'kilometers': int(instance.distance_to_final_location),
            'total_amount': int(
                instance.distance_to_final_location * instance.rate.kilometer
                + instance.duration * instance.rate.minute
                + instance.rate.base
            )
        }
        serializer = PaymentSerializer(data=payment_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return instance
