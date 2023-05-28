from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.gis.db.models import PointField
from django.contrib.gis.measure import Distance

from journey.users.models import Rider, Driver


class Ride(models.Model):
    rider = models.ForeignKey(Rider, on_delete=models.PROTECT, related_name='rides_as_rider')
    diver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='rides_as_driver')
    start = models.DateTimeField(auto_now_add=True)
    starting_location = PointField()
    ends = models.DateTimeField(null=True, blank=True)
    final_location = PointField(null=True, blank=True)
    active = models.BooleanField(default=True)

    @property
    def distance_to_final_location(self):
        if self.final_location is not None:
            return self.starting_location.distance(self.final_location, Distance(km=1))
        return None


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
