from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for journey.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


class Driver(models.Model):
    user = models.ForeignKey(User, verbose_name="user", on_delete=models.PROTECT, related_name="driver_profile")
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self) -> str:
        return self.user.name
    

class Rider(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="rider_profile")
    tokenized_card = models.CharField(max_length=50, null=True, blank=True, help_text="data created in the payment api")

    def __str__(self) -> str:
        return self.user.name
