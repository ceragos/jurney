from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from journey.users.api.views import UserViewSet, RiderViewSet, DriverViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("riders", RiderViewSet)
router.register("drivers", DriverViewSet)


app_name = "api"
urlpatterns = router.urls
