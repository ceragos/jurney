from django.contrib import admin
from journey.rides.models import Rate, Ride

@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    pass


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    pass
