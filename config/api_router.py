from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from journey.users.api.views import UserViewSet, RiderViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet)
router.register("rider", RiderViewSet)


app_name = "api"
urlpatterns = router.urls
