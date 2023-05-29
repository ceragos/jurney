from factory.django import DjangoModelFactory

from journey.rides.models import Rate, Ride

class RateFactory(DjangoModelFactory):
    base = 3500
    minute = 200
    kilometer = 1000

    class Meta:
        model = Rate

class RideFactory(DjangoModelFactory):

    class Meta:
        model = Ride
