from django.contrib import admin
from journey.rides.models import Rate, Ride, Payments

@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    pass


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    pass


@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    pass
