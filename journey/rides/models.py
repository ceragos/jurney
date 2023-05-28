import math

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from journey.users.models import Rider, Driver


class Ride(models.Model):
    rider = models.ForeignKey(Rider, on_delete=models.PROTECT, related_name='rides_as_rider')
    diver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='rides_as_driver')
    start = models.DateTimeField(auto_now_add=True)
    starting_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    starting_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    ends = models.DateTimeField(null=True, blank=True)
    final_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    final_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    active = models.BooleanField(default=True)

    @property
    def distance_to_final_location(self):
        
        earth_radius = 6371

        lat1 = math.radians(self.starting_latitude)
        lon1 = math.radians(self.starting_longitude)
        lat2 = math.radians(self.final_latitude)
        lon2 = math.radians(self.final_longitude)

        lat = lat2 - lat1
        lon = lon2 - lon1

        a = math.sin(lat/2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(lon/2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = earth_radius * c
        return distance


class Rate(models.Model):
    base = models.SmallIntegerField()
    minute = models.SmallIntegerField()
    kilometer = models.SmallIntegerField()
    active = models.BooleanField(default=True)

@receiver(pre_save, sender=Rate)
def deactivate_existing_rates(sender, instance, **kwargs):
    if instance.active:
        Rate.objects.exclude(pk=instance.pk).update(active=False)


class Payments(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.PROTECT, related_name='payment')
    reference = models.CharField(max_length=50)
    minutes_elapsed = models.SmallIntegerField()
    kilometers = models.SmallIntegerField()
    rate = models.ForeignKey(Rate, on_delete=models.PROTECT, related_name='pay_rate')
    total_amount = models.FloatField()
    transaction_response = models.JSONField()
