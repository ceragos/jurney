import math
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from journey.users.api.serializers import UserSerializer, RiderSerializer, RiderPaymentMethodSerializer, DriverSerializer
from journey.users.models import Rider, Driver
from journey.rides.models import Payments, Rate, Ride
from journey.rides.api.serializers import DataPaymentSerializer, RequestRideSerializer, StartRideSerializer, FinisRideSerializer
from journey.utils.distances import calculate_distance
from journey.utils.payment_platform import get_payment_source, generate_transaction, get_transactions
from journey.utils.referrals import generate_payment_reference

User = get_user_model()


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "username"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)
    
class RiderViewSet(ListModelMixin, GenericViewSet):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer

    @action(methods=['patch'], detail=False)
    def payment_method(self, request, *args, **kwargs):
        serializer = RiderPaymentMethodSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        rider = Rider.objects.get(user=user)
        payment_source = get_payment_source(
            serializer.validated_data['tokenized_card'], 
            serializer.validated_data['acceptance_token'], 
            user.email
        )
        if payment_source['status'] != 201:
            return Response(payment_source['data'], status=payment_source['status'])
        
        rider.payment_source = payment_source['payment_source']
        rider.save()

        data = serializer.data
        data['payment_source'] = payment_source['payment_source']

        return Response(data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def request_ride(self, request):
        serializer = RequestRideSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        rider = Rider.objects.get(user=request.user)
        active_rate = Rate.objects.filter(active=True).first()
        rider_lat = serializer.validated_data['latitude']
        rider_lon = serializer.validated_data['longitude']

        data = serializer.data
        drivers = data['drivers']

        min_distance = math.inf
        closest_driver = None

        for driver in drivers:
            distance = calculate_distance(
                rider_lat, rider_lon,
                driver.current_latitude, 
                driver.current_longitude
            )
            if distance < min_distance:
                min_distance = distance
                closest_driver = driver

        ride = Ride(
            rider=rider,
            driver=closest_driver,
            rate=active_rate,
            starting_latitude=rider_lat,
            starting_longitude=rider_lon
        )
        ride.save()

        data = StartRideSerializer(ride).data

        return Response(data, status=status.HTTP_201_CREATED)
    

class DriverViewSet(ListModelMixin, GenericViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

    @action(methods=['patch'], detail=True)
    def finish_ride(self, request, pk=None, *args, **kwargs):
        ride = Ride.objects.filter(id=pk).first()
        serializer = FinisRideSerializer(ride, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        data = {
            'total_amount': instance.payment.total_amount,
            'reference': instance.payment.reference,
            'minutes_elapsed': instance.payment.minutes_elapsed,
            'kilometers': instance.payment.kilometers,
            'transaction_id': instance.payment.transaction_id,
            'status': instance.payment.status,
            'new_latitude': instance.final_latitude,
            'new_longitude': instance.final_longitude
        }

        return Response(data, status=status.HTTP_200_OK)
