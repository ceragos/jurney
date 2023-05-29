from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from journey.users.models import Rider, Driver
from journey.utils.distances import calculate_distance


class Rate(models.Model):
    base = models.SmallIntegerField()
    minute = models.SmallIntegerField()
    kilometer = models.SmallIntegerField()
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Rate {self.id}"

@receiver(pre_save, sender=Rate)
def deactivate_existing_rates(sender, instance, **kwargs):
    if instance.active:
        Rate.objects.exclude(pk=instance.pk).update(active=False)


class Ride(models.Model):
    rider = models.ForeignKey(Rider, on_delete=models.PROTECT, related_name='rides_as_rider')
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='rides_as_driver')
    rate = models.ForeignKey(Rate, on_delete=models.PROTECT, related_name='ride_rates')
    start = models.DateTimeField(auto_now_add=True)
    starting_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    starting_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    ends = models.DateTimeField(null=True, blank=True)
    final_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    final_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Journey of {self.rider}, taken by {self.driver}"

    @property
    def distance_to_final_location(self):
        if self.starting_latitude and self.starting_longitude and self.final_latitude and self.final_longitude:
            distance = calculate_distance(
                self.starting_latitude,
                self.starting_longitude,
                self.final_latitude,
                self.final_longitude
            )
            return distance
        else:
            return None

    @property
    def duration(self):
        if self.start and self.ends:
            duration = int((self.ends - self.start).total_seconds() // 60)
            return duration
        else:
            return None


class Payments(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.PROTECT, related_name='payment')
    reference = models.CharField(max_length=50)
    minutes_elapsed = models.SmallIntegerField()
    kilometers = models.SmallIntegerField()
    total_amount = models.FloatField()
    transaction_id = models.CharField(max_length=25, null=True)
    transaction_response = models.JSONField(null=True)
    transaction_confirmation = models.JSONField(null=True)
    status = models.CharField(max_length=10, null=True)
